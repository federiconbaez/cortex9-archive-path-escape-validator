"""Checks the claims made in PRACTICE.md."""
import unittest

from archive_path_check.core import classify, containment, naive_prefix


class PracticeClaims(unittest.TestCase):
    def test_ex2_same_string_two_profiles(self):
        self.assertEqual(classify("C:x.txt", "posix").verdict, "CONTAINED_LEXICALLY")
        self.assertEqual(classify("C:x.txt", "windows").reason, "DRIVE_RELATIVE")

    def test_ex3_naive_prefix_bug(self):
        self.assertTrue(naive_prefix("/srv/out", "../outx"))
        self.assertFalse(containment("/srv/out", "../outx")["within_components"])

    def test_ex4_dotdot_with_trailing_space_is_unknown_on_windows(self):
        self.assertEqual(classify(".. /x.txt", "windows").reason, "WIN_TRAILING_DOT_OR_SPACE")
        self.assertEqual(classify(".. /x.txt", "posix").verdict, "CONTAINED_LEXICALLY")


if __name__ == "__main__":
    unittest.main()
