"""gh client classification tests (probe run 2 hardening, §20 21:22)."""

import unittest
from unittest import mock

import urllib.error

from ofrenda.gh import GitHub, RateLimited


def http_error(code, headers=None):
    import email.message
    msg = email.message.Message()
    for key, value in (headers or {}).items():
        msg[key] = value
    return urllib.error.HTTPError("https://api.github.com/x", code, "err", msg, None)


class ClassificationTest(unittest.TestCase):
    def test_sustained_403_raises_rate_limited_not_none(self):
        gh = GitHub(token="x")
        with mock.patch.object(gh, "_request", side_effect=http_error(403, {
            "X-RateLimit-Remaining": "4990"
        })), mock.patch("ofrenda.gh.time.sleep"):
            with self.assertRaises(RateLimited):
                gh.get("/repos/axios/axios")

    def test_genuine_404_is_none(self):
        gh = GitHub(token="x")
        with mock.patch.object(gh, "_request", side_effect=http_error(404)), \
             mock.patch("ofrenda.gh.time.sleep"):
            self.assertIsNone(gh.get("/repos/ghost/nope"))

    def test_retry_after_is_honored_then_succeeds(self):
        gh = GitHub(token="x")
        responses = [http_error(403, {
            "X-RateLimit-Remaining": "4990", "Retry-After": "5"
        }), ([1, 2], {})]
        with mock.patch.object(gh, "_request", side_effect=responses), \
             mock.patch("ofrenda.gh.time.sleep") as slept:
            self.assertEqual(gh.get("/repos/x/y"), [1, 2])
            self.assertLessEqual(slept.call_args.args[0], 5.0)

    def test_transport_errors_retry_then_raise(self):
        gh = GitHub(token="x")
        import http.client
        with mock.patch.object(gh, "_request",
                               side_effect=http.client.IncompleteRead(b"")), \
             mock.patch("ofrenda.gh.time.sleep"):
            with self.assertRaises(RateLimited):
                gh.get("/repos/x/y")

    def test_core_exhaustion_sleeps_to_reset(self):
        gh = GitHub(token="x")
        errors = [http_error(403, {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1",   # already past -> tiny wait
        }), ([{"ok": 1}], {})]
        with mock.patch.object(gh, "_request", side_effect=errors), \
             mock.patch("ofrenda.gh.time.sleep"):
            self.assertEqual(gh.get("/repos/x/y"), [{"ok": 1}])


if __name__ == "__main__":
    unittest.main()
