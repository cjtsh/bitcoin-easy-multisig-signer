"""Outbound HTTP policy: TLS stays verified, redirects are refused, and the
configured CA bundle is the one actually trusted."""

import http.server
import ssl
import subprocess
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

import safe_http
from safe_http import open_url
from support import real_ca_bundle


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/ok":
            body = b"genesis"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/dribble":
            # A server that never stops talking but never finishes the response:
            # one byte every 50 ms is far inside any per-socket timeout, so only
            # a total deadline can end the read.
            self.send_response(200)
            self.send_header("Content-Length", "4096")
            self.end_headers()
            for _ in range(30):
                try:
                    self.wfile.write(b"x")
                    self.wfile.flush()
                except OSError:
                    return
                time.sleep(0.05)
        elif self.path in ("/redirect", "/downgrade"):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_address[1]}/ok")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


class _ServerFixture(unittest.TestCase):
    """A loopback HTTP server shared by the test classes below."""

    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()


class SafeHttpTests(_ServerFixture):
    def test_plain_request_succeeds(self):
        with open_url(urllib.request.Request(self.base + "/ok"), timeout=5) as response:
            self.assertEqual(response.read(), b"genesis")

    def test_redirect_is_refused_instead_of_followed(self):
        with self.assertRaises(HTTPError) as caught:
            open_url(urllib.request.Request(self.base + "/redirect"), timeout=5)
        self.assertEqual(caught.exception.code, 302)
        self.assertIn("Refused redirect", str(caught.exception.reason))

    def test_default_tls_context_still_verifies_certificates(self):
        context = ssl.create_default_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)


class DeadlineTests(_ServerFixture):
    """CT-84: a request has a total deadline, not a per-socket timeout.

    ``urllib``'s ``timeout`` arms the *socket*, so every byte that arrives
    re-arms it: a server that sends one byte at a time below that interval can
    hold a connection open indefinitely. The read loop therefore checks a
    monotonic clock around the whole response.
    """

    def test_a_normal_read_is_unchanged(self):
        deadline = safe_http.Deadline(5.0)
        with open_url(urllib.request.Request(self.base + "/ok"), timeout=5,
                      deadline=deadline) as response:
            self.assertEqual(safe_http.read_bounded(response, 4096, deadline),
                             b"genesis")

    def test_a_read_without_a_deadline_is_a_plain_bounded_read(self):
        with open_url(urllib.request.Request(self.base + "/ok"), timeout=5) as response:
            self.assertEqual(safe_http.read_bounded(response, 4096), b"genesis")

    def test_one_byte_past_the_limit_is_returned_so_oversize_is_detectable(self):
        # Every caller keeps its own "len(body) > limit" check; the extra byte
        # is what makes an over-large body detectable rather than truncated.
        deadline = safe_http.Deadline(5.0)
        with open_url(urllib.request.Request(self.base + "/ok"), timeout=5,
                      deadline=deadline) as response:
            body = safe_http.read_bounded(response, 3, deadline)
        self.assertEqual(body, b"gene")

    def test_a_dribbling_server_cannot_outlive_the_deadline(self):
        # The socket timeout (5 s) is much larger than the deadline (1 s), and
        # every byte arrives within 50 ms, so the socket timeout can never fire:
        # only the total deadline can end this read.
        deadline = safe_http.Deadline(1.0)
        started = time.monotonic()
        with open_url(urllib.request.Request(self.base + "/dribble"), timeout=5,
                      deadline=deadline) as response:
            with self.assertRaises(TimeoutError) as caught:
                safe_http.read_bounded(response, 4096, deadline)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 4.0, "the read outlived its deadline")
        self.assertIn("deadline", str(caught.exception))

    def test_an_expired_deadline_is_refused_before_connecting(self):
        deadline = safe_http.Deadline(0.0)
        self.assertTrue(deadline.expired())
        with self.assertRaises(TimeoutError):
            open_url(urllib.request.Request(self.base + "/ok"), timeout=5,
                     deadline=deadline)

    def test_remaining_never_grows(self):
        deadline = safe_http.Deadline(1.0)
        first = deadline.remaining()
        time.sleep(0.02)
        self.assertLessEqual(deadline.remaining(), first)


class TrustStoreTests(_ServerFixture):
    """The CA store the app configures must actually be the one it trusts.

    A frozen app sets its bundle inside ``main()``, after imports. Because urllib
    builds an ``SSLContext`` eagerly when an ``HTTPSHandler`` is constructed,
    building the opener at import time captured the host's ambient trust settings
    and silently ignored the bundled store. HTTPS therefore worked only on
    machines that happened to have CA files where OpenSSL looked for them, and
    failed everywhere else -- while still passing the build machine's self-check.
    """

    def setUp(self):
        self.addCleanup(safe_http.set_trust_bundle, "/nonexistent/restore.pem")

    def test_importing_safe_http_builds_no_ssl_context(self):
        code = ("import safe_http, sys;"
                "sys.exit(0 if safe_http._client is None else 1)")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True)
        self.assertEqual(result.returncode, 0,
                         "importing safe_http must not build an SSL context")

    def test_setting_a_bundle_drops_any_cached_opener(self):
        with open_url(urllib.request.Request(self.base + "/ok"), timeout=5) as response:
            self.assertEqual(response.read(), b"genesis")
        self.assertIsNotNone(safe_http._client)
        safe_http.set_trust_bundle(real_ca_bundle() or "/nonexistent/reset.pem")
        self.assertIsNone(safe_http._client,
                          "a newly configured bundle must invalidate the opener")

    def test_a_real_bundle_contributes_trusted_cas(self):
        bundle = real_ca_bundle()
        if bundle is None:
            self.skipTest("no system CA bundle available to test with")
        safe_http.set_trust_bundle(bundle)
        self.assertEqual(safe_http.trust_bundle(), bundle)
        self.assertGreater(safe_http.loaded_ca_count(), 0,
                           "the configured bundle must contribute trusted CAs")

    def test_a_missing_bundle_is_ignored_rather_than_crashing(self):
        safe_http.set_trust_bundle("/definitely/not/here.pem")
        self.assertIsNone(safe_http.trust_bundle())
        safe_http.loaded_ca_count()  # must not raise


if __name__ == "__main__":
    unittest.main()
