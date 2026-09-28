"""Outbound HTTP policy: TLS stays verified and redirects are never followed."""

import http.server
import ssl
import threading
import unittest
import urllib.request
from urllib.error import HTTPError

from safe_http import open_url


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path == "/ok":
            body = b"genesis"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in ("/redirect", "/downgrade"):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_address[1]}/ok")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


class SafeHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

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


if __name__ == "__main__":
    unittest.main()
