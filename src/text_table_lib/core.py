"""Core table rendering with wide-character aware alignment.

The central problem is that Python's str formatting counts code points, not
terminal columns.  A CJK ideograph occupies two columns in most terminals but
len() == 1, so a table built with str.ljust looks ragged.  We therefore measure
with a small wcwidth-style function and pad by columns, not characters.

The trade-off: we ship a compact East Asian Width table rather than a full
Unicode database.  Characters outside the table are treated as width 1.  That
keeps the library dependency-free and the binary small; it is correct for the
common cases (ASCII, Latin-1, CJK, Hangul, fullwidth forms) and degrades
predictably elsewhere.
"""

from __future__ import annotations

import unicodedata
from typing import Iterable, List, Sequence

__all__ = ["Table", "render", "display_width", "pad"]


def _is_wide(ch: str) -> bool:
    """Return True if *ch* should occupy two terminal columns.

    We use the standard East Asian Width property via unicodedata, which is
    stdlib and already carries the Unicode tables.  Only the ranges that are
    actually wide in terminals are considered; ambiguous characters are left
    at width 1 because that matches the default of most modern terminals.
    """
    if not ch:
        return False
    ea = unicodedata.east_asian_width(ch)
    return ea in ("W", "F")


def display_width(text: str) -> int:
    """Return the number of terminal columns *text* occupies.

    Control characters are counted as width 0 because they do not advance the
    cursor in a well-behaved terminal; combining marks likewise add nothing
    because they attach to the preceding character.  We do not attempt to
    interpret other control sequences.
    """
    total = 0
    for ch in text:
        if ch == "\t":
            # Tabs are not expanded here; callers should expand them first.
            # Counting a tab as one column keeps the function total and
            # deterministic, which is what alignment code needs.
            total += 1
        elif unicodedata.category(ch) == "Cc":
            total += 0
        elif unicodedata.combining(ch):
            total += 0
        elif _is_wide(ch):
            total += 2
        else:
            total += 1
    return total


def pad(text: str, width: int, align: str = "left") -> str:
    """Pad *text* with spaces to *width* terminal columns.

    ``align`` is one of ``"left"``, ``"right"`` or ``"center"``.  If *text*
    is already wider than *width* it is returned unchanged; truncation is the
    caller's decision because silently cutting text loses information.
    """
    if align not in ("left", "right", "center"):
        raise ValueError(f"unknown alignment: {align!r}")
    current = display_width(text)
    if current >= width:
        return text
    missing = width - current
    if align == "left":
        return text + " " * missing
    if align == "right":
        return " " * missing + text
    left = missing // 2
    right = missing - left
    return " " * left + text + " " * right


def _coerce_rows(rows: Iterable[Sequence[object]]) -> List[List[str]]:
    """Turn arbitrary cell values into strings, preserving row order."""
    out: List[List[str]] = []
    for row in rows:
        out.append(["" if cell is None else str(cell) for cell in row])
    return out


class Table:
    """A text table that aligns columns by display width.

    The table is built from a header row and zero or more data rows.  Column
    widths are the maximum display width of the cells in that column.  A
    single space separates columns and a border of ``|`` and ``-`` frames the
    result.
    """

    def __init__(
        self,
        headers: Sequence[object],
        rows: Iterable[Sequence[object]] = (),
        aligns: Sequence[str] | None = None,
    ) -> None:
        self.headers = ["" if h is None else str(h) for h in headers]
        self.rows = _coerce_rows(rows)
        ncols = len(self.headers)
        if aligns is None:
            self.aligns = ["left"] * ncols
        else:
            self.aligns = list(aligns)
            if len(self.aligns) != ncols:
                raise ValueError("aligns must have one entry per column")
            for a in self.aligns:
                if a not in ("left", "right", "center"):
                    raise ValueError(f"unknown alignment: {a!r}")
        for row in self.rows:
            if len(row) != ncols:
                raise ValueError("every row must match the header width")

    def widths(self) -> List[int]:
        """Return the display width of each column."""
        widths = [display_width(h) for h in self.headers]
        for row in self.rows:
            for i, cell in enumerate(row):
                w = display_width(cell)
                if w > widths[i]:
                    widths[i] = w
        return widths

    def render(self) -> str:
        """Render the table as a single string with trailing newline."""
        widths = self.widths()
        lines: List[str] = []
        lines.append(self._rule(widths))
        lines.append(self._format_row(self.headers, widths))
        lines.append(self._rule(widths))
        for row in self.rows:
            lines.append(self._format_row(row, widths))
        lines.append(self._rule(widths))
        return "\n".join(lines) + "\n"

    def _format_row(self, cells: Sequence[str], widths: Sequence[int]) -> str:
        padded = [
            pad(cell, widths[i], self.aligns[i]) for i, cell in enumerate(cells)
        ]
        return "| " + " | ".join(padded) + " |"

    def _rule(self, widths: Sequence[int]) -> str:
        return "+-" + "-+-".join("-" * w for w in widths) + "-+"


def render(
    headers: Sequence[object],
    rows: Iterable[Sequence[object]] = (),
    aligns: Sequence[str] | None = None,
) -> str:
    """Convenience wrapper around :class:`Table`."""
    return Table(headers, rows, aligns).render()
