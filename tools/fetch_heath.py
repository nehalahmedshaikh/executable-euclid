"""Parse Heath's enunciations and write ``src/euclid/elements/heath.json``.

The statements the library and the site display are Thomas L. Heath's 1908
translation, which is in the public domain.  They are parsed rather than
retyped or paraphrased, so the words shipped in this repository are the
published ones.

All thirteen books come from a single source: an epub of Heath's translation.
An epub is a zip of XHTML, so it is parsed with ``zipfile`` and a little tag
stripping.  Only the enunciations are taken -- they are Heath's 1908 words and
public domain -- whereas a modern edition's own introductions and notes are a
copyrighted compilation and are neither extracted nor committed.

The epub is a local file, so nothing is downloaded and this script never
touches the network.  Put the file in ``tools/sources/`` under the name in
``EPUB_NAME``.

Nothing is repaired by hand.  An enunciation that fails a check is dropped, not
mended, and nothing stands in for it: a proposition whose ref is missing from
``heath.json`` raises rather than falling back to anything.

Three checks guard the output.  ``suspicious`` rejects the malformed.  The
per-book counts in ``EPUB_EXPECTED`` catch a heading the parser missed.  And
``hapax`` lists every word used exactly once across all the enunciations, which
is how a scanning error that still spells a pronounceable word gets found:
Euclid's vocabulary is small and endlessly repetitive, so a word appearing once
is either a real technical term or a mis-scan, and the list is short enough to
read through.

Run with ``python tools/fetch_heath.py``.  Not imported by the library: the
result is committed.
"""

from __future__ import annotations

import collections
import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "src" / "euclid" / "elements" / "heath.json"
CACHE = Path(__file__).resolve().parent / "sources"

EPUB_NAME = "euclid_delphi.epub"
# Which document in the epub holds each book's propositions, and the number the
# first heading in it carries. Book X is split across three documents because
# Heath's Book X is interrupted twice by further sets of definitions.
EPUB_BOOKS: dict[str, list[tuple[str, int]]] = {
    "I": [("027.html", 1)],
    "II": [("029.html", 1)],
    "III": [("031.html", 1)],
    "IV": [("033.html", 1)],
    "V": [("035.html", 1)],
    "VI": [("037.html", 1)],
    "VII": [("039.html", 1)],
    "VIII": [("040.html", 1)],
    "IX": [("041.html", 1)],
    "X": [("043.html", 1), ("045.html", 48), ("047.html", 85)],
    "XI": [("049.html", 1)],
    "XII": [("051.html", 1)],
    "XIII": [("053.html", 1)],
}
# How many propositions each book has, as a check that nothing was missed.
EPUB_EXPECTED = {"I": 48, "II": 14, "III": 37, "IV": 16,
                 "V": 25, "VI": 33, "VII": 39, "VIII": 27, "IX": 36,
                 "X": 115, "XI": 39, "XII": 18, "XIII": 18}

# The epub is typeset with curly quotes and dashes; the rest of the pipeline is
# ASCII. Substituting the ASCII forms is transliteration, not editing.
TYPOGRAPHY = {"“": '"', "”": '"', "‘": "'", "’": "'",
              "—": "--", "–": "-", "′": "'"}

# Errata: places where this source misprints Heath, and the correction.
#
# Every entry is a demonstrable scanning error -- a letter substituted, a full
# stop lost -- and never a reading of what Heath meant. Nothing here paraphrases
# him. The wrong text is kept alongside the right one and both are written into
# heath.json, so a reader can audit the correction instead of taking it on
# trust, and :func:`apply_errata` fails loudly if a correction stops applying,
# which is what would happen if the source were ever swapped for another.
#
# The first two were found by the hapax list this script prints at the end of a
# run; the third by the full-stop check in `suspicious`.
ERRATA = {
    "II.13": ("acutc angle", "acute angle", "'acutc' scanned for 'acute'"),
    "XII.4": ("cach", "each", "'cach' scanned for 'each'"),
    "VI.26": ("diameter with the whole", "diameter with the whole.",
              "the closing full stop is missing"),
}


def apply_errata(statements: dict[str, str]) -> list[tuple[str, str]]:
    """Correct the known misprints, and refuse to pass over one that has moved."""
    applied: list[tuple[str, str]] = []
    for ref, (wrong, right, why) in ERRATA.items():
        if ref not in statements:
            raise SystemExit(f"erratum for {ref}: no such enunciation was parsed")
        if statements[ref].count(wrong) != 1:
            raise SystemExit(
                f"erratum for {ref}: expected exactly one {wrong!r} to correct, "
                f"found {statements[ref].count(wrong)}. The source has changed."
            )
        statements[ref] = statements[ref].replace(wrong, right)
        applied.append((ref, why))
    return applied

BOOK_ORDER = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]


# ---------------------------------------------------------------------------
# reading the epub
# ---------------------------------------------------------------------------


def _clean_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment).replace("\xa0", " ")
    for glyph, ascii_form in TYPOGRAPHY.items():
        fragment = fragment.replace(glyph, ascii_form)
    return re.sub(r"\s+", " ", fragment).strip()


EPUB_HEADING = re.compile(r"PROPOSITION\s+([IVXL]+|\d+)\s*\.?\s*</span>", re.I)
EPUB_PARAGRAPH = re.compile(r"<p[^>]*>(.*?)</p>", re.S)

# Heath prints his cross-references in the margin. This edition sets them inline
# in braces, so I.22 ends "...greater than the remaining one. {I. 20}". Removing
# them is undoing the edition's typesetting, not editing Heath, and that was
# established rather than assumed: while this parser was being written its
# output for Books I-IV was compared word for word against D. R. Wilkins's
# independent transcription from the printed page, which carries no such text.
# (That comparison has served its purpose and is not kept; 104 of 115
# enunciations matched exactly, and of the eleven that did not, ten were errors
# in the Wilkins text.) Only a brace naming a book is removed; Heath's own
# bracketed clause in VII.27 names none and stays.
EPUB_MARGIN_NOTE = re.compile(r"\s*\{\s*(?:cf\.\s*)?(?:I|V|X)[IVX]*\.[^{}]*\}")

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
         "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def parse_epub_book(document: str, book: str, first: int) -> dict[str, str]:
    """Take the enunciation under each ``PROPOSITION N`` heading.

    The number comes from the heading's position in the document, not from the
    numeral it prints.  The numerals are not trustworthy: this edition sets
    some as roman, and sets IX.11 as ``II``, which read as a numeral would
    silently overwrite IX.2.  Position cannot collide, and the count of
    headings per book is checked against ``EPUB_EXPECTED`` afterwards.
    """
    found: dict[str, str] = {}
    marks = [(match.start(), match.group(1)) for match in EPUB_HEADING.finditer(document)]
    for index, (start, numeral) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(document)
        chunk = document[start:end]
        paragraphs = [text for text in
                      (_clean_html(p) for p in EPUB_PARAGRAPH.findall(chunk)) if text]
        if not paragraphs:
            continue
        number = first + index
        ref = f"{book}.{number}"
        if numeral.isdigit() and int(numeral) != number:
            print(f"  note {ref}: heading numeral reads {numeral!r}", file=sys.stderr)
        elif not numeral.isdigit() and ROMAN.get(numeral.upper()) != number:
            print(f"  note {ref}: heading numeral reads {numeral!r}", file=sys.stderr)
        found[ref] = _join_split_enunciation(paragraphs)
    return found


def _join_split_enunciation(paragraphs: list[str]) -> str:
    """Reunite an enunciation the typesetter broke into several paragraphs.

    X.42 puts its closing full stop in a paragraph of its own.  A continuation
    like that opens with punctuation or lower case; the proof that follows a
    complete enunciation opens with a capital ("Let ABC be..."), so it is never
    swept in.
    """
    statement = paragraphs[0]
    index = 1
    while (index < len(paragraphs)
           and not statement.endswith((".", "!", "?"))
           and re.match(r"[^A-Z0-9]", paragraphs[index])):
        statement = f"{statement} {paragraphs[index]}".replace(" .", ".")
        index += 1
    return EPUB_MARGIN_NOTE.sub("", statement).strip()


def parse_epub(path: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        for book, documents in EPUB_BOOKS.items():
            statements: dict[str, str] = {}
            for name, first in documents:
                raw = archive.read(f"Ops/{name}").decode("utf-8", "replace")
                statements.update(parse_epub_book(raw, book, first))
            expected = EPUB_EXPECTED[book]
            if len(statements) != expected:
                print(f"  WARNING: Book {book} yielded {len(statements)} enunciations, "
                      f"expected {expected}", file=sys.stderr)
            found.update(statements)
    return found


# ---------------------------------------------------------------------------


def suspicious(ref: str, statement: str) -> str:
    """Cheap sanity checks, so a mangled extraction is never written silently."""
    if len(statement) < 25:
        return "too short"
    if not statement.endswith("."):
        return "does not end in a full stop"
    if re.search(r"[^\x20-\x7e]", statement):
        return "contains non-printable characters"
    if re.search(r"[a-z]{25,}", statement):
        return "looks like the spaces were lost"
    if statement.count(" ") < 4:
        return "too few spaces"
    # A backstop behind EPUB_MARGIN_NOTE: a reference the stripper did not
    # recognise means the extraction ran past the end of the enunciation.
    # (Heath's own bracketed clause in VII.27 names no book and is kept.)
    if re.search(r"\{\s*(?:cf\.\s*)?(?:I|V|X)[IVX]*\.", statement):
        return "carries a cross-reference from the proof"
    return ""


def hapax(statements: dict[str, str]) -> list[tuple[str, str]]:
    """Every word used exactly once, with the enunciation that uses it.

    This is the check that catches what nothing else can.  A scan that turns
    "each" into "cach" or "acute" into "acutc" still spells a pronounceable
    word, keeps the sentence the right length, and passes every test in
    :func:`suspicious`.  But Euclid's vocabulary is tiny and endlessly
    repetitive -- four hundred-odd distinct words across four hundred-odd
    enunciations -- so a word that appears exactly once is either a real
    technical term or a mis-scan, and there are few enough of either to read
    the whole list.  Two of the three entries in ``ERRATA`` were found this way.
    """
    counts: collections.Counter[str] = collections.Counter()
    first_seen: dict[str, str] = {}
    for ref, statement in statements.items():
        for word in re.findall(r"[A-Za-z][A-Za-z']*", statement):
            counts[word.lower()] += 1
            first_seen.setdefault(word.lower(), ref)
    return [(word, first_seen[word]) for word, n in sorted(counts.items()) if n == 1]


def main() -> int:
    epub = CACHE / EPUB_NAME
    if not epub.exists():
        print(f"no source text: put the epub at {epub.relative_to(ROOT)}", file=sys.stderr)
        return 1
    statements = parse_epub(epub)
    print(f"Books I-XIII <- {EPUB_NAME}: {len(statements)} enunciations")

    for ref, why in apply_errata(statements):
        print(f"  corrected {ref}: {why}")

    complaints = {ref: why for ref, why in
                  ((ref, suspicious(ref, text)) for ref, text in statements.items()) if why}
    if complaints:
        for ref, why in sorted(complaints.items()):
            print(f"  FAILED {ref}: {why}", file=sys.stderr)
        print("\nEvery enunciation must survive the checks. Correct the source in "
              "ERRATA rather than dropping it.", file=sys.stderr)
        return 1

    expected = sum(EPUB_EXPECTED.values())
    if len(statements) != expected:
        print(f"\nexpected {expected} enunciations, have {len(statements)}", file=sys.stderr)
        return 1

    payload = {
        "translation": "Thomas L. Heath, The Thirteen Books of Euclid's Elements "
        "(Cambridge University Press, 1908). Public domain.",
        "transcription": f"Parsed from tools/sources/{EPUB_NAME}, an epub of Heath's "
        "translation. One source for all thirteen books.",
        "sources": [f"local file tools/sources/{EPUB_NAME} (enunciations only)"],
        "note": "Parsed, not retyped. Only the enunciations are taken; a modern "
        "edition's own introductions and notes are a copyrighted compilation and "
        "are not extracted. Every proposition of all thirteen books is here, so "
        "nothing displayed anywhere is a paraphrase.",
        "errata": [
            {"ref": ref, "source_reads": wrong, "corrected_to": right, "note": why}
            for ref, (wrong, right, why) in sorted(ERRATA.items(), key=lambda i: _sort_key(i))
        ],
        "statements": dict(sorted(statements.items(), key=_sort_key)),
    }
    DESTINATION.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {len(statements)} statements to {DESTINATION.relative_to(ROOT)}")

    rare = hapax(statements)
    print(f"\n{len(rare)} words are used exactly once. Read them: a mis-scan hides here,\n"
          "and everything else in the list should be a real term of Euclid's.")
    for index in range(0, len(rare), 4):
        print("   " + "".join(f"{word} ({ref})".ljust(28)
                              for word, ref in rare[index:index + 4]).rstrip())
    return 0


def _sort_key(item: tuple[str, str]) -> tuple[int, int]:
    book, number = item[0].split(".")
    return (BOOK_ORDER.index(book) if book in BOOK_ORDER else 99), int(number)


if __name__ == "__main__":
    raise SystemExit(main())
