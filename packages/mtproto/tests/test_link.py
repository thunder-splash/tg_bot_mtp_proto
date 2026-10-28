import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mtproto import parse_proxy_url, build_ee_secret, mask_secret
from mtproto.secret import parse_secret


class TestMtproto(unittest.TestCase):
    def test_ee_link_customer(self):
        url = (
            "https://t.me/proxy?server=187.124.67.86&port=8443"
            "&secret=ee0b2ecc76981b874c23eb241d3522fd433138372e3132342e36372e3836"
        )
        ep = parse_proxy_url(url)
        self.assertEqual(ep.host, "187.124.67.86")
        self.assertEqual(ep.port, 8443)
        self.assertEqual(ep.secret.key_hex, "0b2ecc76981b874c23eb241d3522fd43")
        self.assertEqual(ep.secret.domain, "187.124.67.86")
        self.assertEqual(ep.mtproxybot_secret, "0b2ecc76981b874c23eb241d3522fd43")
        self.assertTrue(ep.tg_link.startswith("tg://proxy?"))

    def test_build_ee(self):
        s = build_ee_secret("0b2ecc76981b874c23eb241d3522fd43", "www.cloudflare.com")
        parsed = parse_secret(s)
        self.assertEqual(parsed.domain, "www.cloudflare.com")

    def test_mask(self):
        self.assertEqual(mask_secret("eeabcdef12345678"), "ee****5678")


if __name__ == "__main__":
    unittest.main()
