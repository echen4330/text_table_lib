import unittest

from text_table_lib import Table, render, display_width, pad


class DisplayWidthTests(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(display_width("abc"), 3)

    def test_empty(self):
        self.assertEqual(display_width(""), 0)

    def test_cjk_is_two_columns(self):
        self.assertEqual(display_width("\u4f60\u597d"), 4)

    def test_combining_mark_is_zero(self):
        # 'e' + combining acute should be one column, not two.
        self.assertEqual(display_width("e\u0301"), 1)

    def test_control_char_is_zero(self):
        self.assertEqual(display_width("a\x00b"), 2)

    def test_tab_counts_as_one(self):
        self.assertEqual(display_width("\t"), 1)


class PadTests(unittest.TestCase):
    def test_left(self):
        self.assertEqual(pad("ab", 5, "left"), "ab   ")

    def test_right(self):
        self.assertEqual(pad("ab", 5, "right"), "   ab")

    def test_center_odd_extra_goes_right(self):
        self.assertEqual(pad("ab", 5, "center"), " ab  ")

    def test_wide_text_pads_by_columns(self):
        # Two CJK chars are four columns; pad to six adds two spaces.
        self.assertEqual(pad("\u4f60\u597d", 6, "left"), "\u4f60\u597d  ")

    def test_no_truncation(self):
        self.assertEqual(pad("abcdef", 3, "left"), "abcdef")

    def test_unknown_alignment_raises(self):
        with self.assertRaises(ValueError):
            pad("a", 3, "middle")


class TableTests(unittest.TestCase):
    def test_simple_render(self):
        table = Table(["Name", "Age"], [["Alice", 30], ["Bob", 7]])
        expected = (
            "+-------+-----+\n"
            "| Name  | Age |\n"
            "+-------+-----+\n"
            "| Alice | 30  |\n"
            "| Bob   | 7   |\n"
            "+-------+-----+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_wide_character_alignment(self):
        table = Table(["Word", "Meaning"], [["\u4f60\u597d", "hello"]])
        expected = (
            "+------+---------+\n"
            "| Word | Meaning |\n"
            "+------+---------+\n"
            "| \u4f60\u597d | hello   |\n"
            "+------+---------+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_right_alignment(self):
        table = Table(["N"], [[1], [22]], aligns=["right"])
        expected = (
            "+----+\n"
            "|  N |\n"
            "+----+\n"
            "|  1 |\n"
            "| 22 |\n"
            "+----+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_center_alignment(self):
        table = Table(["X"], [["a"], ["bb"]], aligns=["center"])
        expected = (
            "+----+\n"
            "| X  |\n"
            "+----+\n"
            "| a  |\n"
            "| bb |\n"
            "+----+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_no_rows(self):
        table = Table(["A", "B"])
        expected = (
            "+---+---+\n"
            "| A | B |\n"
            "+---+---+\n"
            "+---+---+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_none_becomes_empty(self):
        table = Table(["A"], [[None]])
        expected = (
            "+---+\n"
            "| A |\n"
            "+---+\n"
            "|   |\n"
            "+---+\n"
        )
        self.assertEqual(table.render(), expected)

    def test_row_width_mismatch_raises(self):
        with self.assertRaises(ValueError):
            Table(["A", "B"], [["only-one"]])

    def test_aligns_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            Table(["A", "B"], aligns=["left"])

    def test_render_function_matches_table(self):
        headers = ["H"]
        rows = [["v"]]
        self.assertEqual(render(headers, rows), Table(headers, rows).render())


if __name__ == "__main__":
    unittest.main()
