"""No real wallet, explorer, or broadcast calls in network settings tests."""

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from network_config import NETWORKS
from network_settings import (
    SettingsError, default_servers, load_servers, save_servers,
    validate_esplora_url, verify_esplora,
)
from support import assert_private_file


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        path_patch = patch("network_settings.settings_path", return_value=self.path)
        path_patch.start()
        self.addCleanup(path_patch.stop)

    def test_default_persistence_and_invalid_electrum_url(self):
        self.assertEqual(load_servers(), default_servers())
        servers = default_servers()
        servers["main"]["explorer"] = "https://explorer.btc21.cc/api"
        save_servers(servers)
        self.assertEqual(load_servers(), servers)
        self.assertNotIn("address", self.path.read_text())
        for url in ("https://electrum.btc21.cc/", "http://remote.example/api",
                    # A credential-shaped URL on purpose: this asserts the app
                    # refuses one, so the scanner is told not to report it.
                    "https://name:password@example.org/api"):  # pragma: allowlist secret
            with self.subTest(url=url), self.assertRaises(SettingsError):
                validate_esplora_url(url)
        self.assertEqual(validate_esplora_url("http://127.0.0.1:3000/api/"),
                         "http://127.0.0.1:3000/api")

    def test_custom_endpoint_must_return_selected_chain_genesis(self):
        class Response(io.BytesIO):
            length = 64
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                self.close()
        for chain in NETWORKS:
            answers = [NETWORKS[chain].genesis_hash]
            if NETWORKS[chain].checkpoint_hash:
                answers.append(NETWORKS[chain].checkpoint_hash)
            with self.subTest(chain=chain), patch(
                "network_settings.urlopen",
                side_effect=[Response(answer.encode()) for answer in answers],
            ) as fetch:
                verify_esplora(chain, "https://custom.example/api")
                self.assertEqual(fetch.call_args_list[0].args[0].full_url,
                                 "https://custom.example/api/block-height/0")
            other = "main" if chain == "testnet4" else "testnet4"
            with patch("network_settings.urlopen",
                       return_value=Response(NETWORKS[other].genesis_hash.encode())):
                with self.assertRaisesRegex(SettingsError, "wrong Bitcoin network"):
                    verify_esplora(chain, "https://custom.example/api")

    def test_mutinynet_refuses_standard_signet_even_with_shared_genesis(self):
        class Response(io.BytesIO):
            length = 64
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                self.close()
        standard_signet_block_one = (
            "00000086d6b2636cb2a392d45edc4ec544a10024d30141c9adf4bfd9de533b53")
        with patch("network_settings.urlopen", side_effect=[
            Response(NETWORKS["mutinynet"].genesis_hash.encode()),
            Response(standard_signet_block_one.encode()),
        ]):
            with self.assertRaisesRegex(SettingsError, "wrong Bitcoin network"):
                verify_esplora("mutinynet", "https://ordinary-signet.example/api")

    def test_corrupt_settings_do_not_silently_switch_to_public_defaults(self):
        self.path.write_text('{"version": 1, "servers": []}')
        with self.assertRaises(SettingsError):
            load_servers()

    def test_old_two_network_settings_keep_existing_choices(self):
        old = default_servers()
        old.pop("mutinynet")
        old["main"]["explorer"] = "https://private.example/api"
        self.path.write_text(json.dumps({"version": 1, "servers": old}))
        loaded = load_servers()
        self.assertEqual(loaded["main"]["explorer"], "https://private.example/api")
        self.assertEqual(loaded["mutinynet"], default_servers()["mutinynet"])

    def test_the_settings_file_is_written_privately(self):
        """The saved server choices are never world-readable (CT-09).

        POSIX: mode 0600. Windows: inside the user's profile (the ACL there).
        One rule, asserted through the app's own ``assert_private_file``.
        """
        save_servers(default_servers())
        assert_private_file(self, self.path)
        self.assertEqual(load_servers(), default_servers())


class PublishedChainConstantsTests(unittest.TestCase):
    """CT-78: the chain constants are correct, and until now nothing said so.

    Every other case in this file builds its expectation *from* NETWORKS, so a
    true-value swap (mainnet's genesis replaced by Signet's) agreed with the
    suite and a mocked Signet explorer passed ``verify_esplora("main")``. These
    pins are the published values written out literally, so a swap has to fight
    a literal instead of agreeing with itself.
    """

    # (genesis hash, checkpoint height, checkpoint hash), pinned verbatim.
    PUBLISHED = {
        # BIP-122 / Bitcoin Core mainnet chainparams (`bitcoind getblockhash 0`).
        "main": ("000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
                 None, None),
        # BIP-94 testnet4 genesis.
        "testnet4": ("00000000da84f2bafbbc53dee25a72ae507ff4914b867c565be350b0da8bf043",
                     None, None),
        # Mutinynet is a custom Signet: it shares ordinary Signet's genesis, so
        # block 1 is pinned as well (captured from the public Esplora API on
        # 2026-09-29; see releases/MUTINYNET-0.3.0.md).
        "mutinynet": ("00000008819873e925422c1ff0f99f7cc9bbb232af63a077a480a3633bee1ef6",
                      1,
                      "000002855893a0a9b24eaffc5efc770558a326fee4fc10c9da22fc19cd2954f9"),
    }

    def test_the_published_chain_constants_are_pinned_verbatim(self):
        self.assertEqual(set(NETWORKS), set(self.PUBLISHED))
        for chain, (genesis, height, checkpoint) in self.PUBLISHED.items():
            with self.subTest(chain=chain):
                config = NETWORKS[chain]
                self.assertEqual(config.genesis_hash, genesis)
                self.assertEqual(config.checkpoint_height, height)
                self.assertEqual(config.checkpoint_hash, checkpoint)

    def test_the_network_to_genesis_mapping_is_exclusive(self):
        """No two networks share a genesis, and the chainparams agree with it."""
        genesis = [config.genesis_hash for config in NETWORKS.values()]
        self.assertEqual(len(genesis), len(set(genesis)))
        # Mutinynet and ordinary Signet share a genesis, so the block-1
        # checkpoint is the only thing telling them apart; it must survive.
        self.assertIsNotNone(NETWORKS["mutinynet"].checkpoint_hash)
        self.assertEqual(NETWORKS["mutinynet"].checkpoint_height, 1)

    def test_a_signet_genesis_is_not_accepted_as_mainnet(self):
        """The swap CT-78 was written for: mainnet asked, Signet answered."""
        class Response(io.BytesIO):
            length = 64
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                self.close()
        signet_genesis = self.PUBLISHED["mutinynet"][0]
        with patch("network_settings.urlopen",
                   return_value=Response(signet_genesis.encode())):
            with self.assertRaisesRegex(SettingsError, "wrong Bitcoin network"):
                verify_esplora("main", "https://ordinary-signet.example/api")


if __name__ == "__main__":
    unittest.main()
