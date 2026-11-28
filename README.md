# text_table_lib

Render aligned text tables that survive wide characters.

```python
from text_table_lib import Table, render

# Using the class
print(Table(["Name", "Age"], [["Alice", 30], ["Bob", 7]]).render())

# Or the convenience function
print(render(["Word", "Meaning"], [["\u4f60\u597d", "hello"]]))
```

The output uses `|` separators and `-` rules:

```
+-------+-----+
| Name  | Age |
+-------+-----+
| Alice | 30  |
| Bob   | 7   |
+-------+-----+
```

## Why this exists

Python's `str.ljust` and friends count code points, not terminal columns.  A
CJK ideograph is one code point but two columns wide, so a table padded with
`ljust` looks ragged the moment any cell contains non-Latin text.  This library
measures each cell with a width function and pads by columns instead.

The trade-off is that we rely on `unicodedata.east_asian_width` rather than a
full wcwidth database.  That keeps the library dependency-free and correct for
the common cases (ASCII, Latin-1, CJK, Hangul, fullwidth forms).  Characters
whose width is ambiguous are treated as one column, which matches the default
behaviour of most modern terminals.

## The awkward edge

Tabs are counted as a single column.  If your data contains tabs, expand them
before building the table; the library will not guess a tab stop.  Likewise,
the library does not truncate cells that are wider than their column, because
silently cutting text loses information.  Column widths are always the maximum
of the cells they contain.

## API

- `Table(headers, rows=(), aligns=None)` — build a table.  `headers` and each
  row are sequences of values; `None` becomes the empty string.  `aligns` is an
  optional sequence of `"left"`, `"right"` or `"center"`, one per column.
- `Table.render()` — return the rendered table as a string ending in a newline.
- `render(headers, rows=(), aligns=None)` — convenience wrapper around `Table`.
- `display_width(text)` — number of terminal columns `text` occupies.
- `pad(text, width, align="left")` — pad `text` to `width` columns.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

