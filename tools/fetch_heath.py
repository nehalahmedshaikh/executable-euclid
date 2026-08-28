"""Fetch Heath's enunciations and write ``src/euclid/elements/heath.json``.

The statements the library and the site display are Thomas L. Heath's 1908
translation, which is in the public domain.  They are downloaded and parsed
rather than retyped or paraphrased, so the words shipped in this repository
are the published ones.

Sources, both transcriptions by D. R. Wilkins (Trinity College Dublin):

* Book I -- an HTML edition with each enunciation in its own tagged element,
  which makes extraction exact rather than heuristic.
* Books II, III, IV -- typeset PDFs.  Text extraction needs two repairs: PDF
  stores inter-word gaps as kerning numbers rather than spaces, and TeX encodes
  ligatures as control characters.  Both are handled below, and every extracted
  enunciation is sanity-checked before being written.

Books V onwards are not covered by these sources.  Propositions absent from the
output file keep the short editorial summaries carried in the code, and
everything that displays a statement says which of the two it is showing.

Run with ``python tools/fetch_heath.py``.  Not imported by the library: the
result is committed, so nothing needs the network at run time.
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "src" / "euclid" / "elements" / "heath.json"
CACHE = Path(__file__).resolve().parent / "sources"

BOOK_ONE = (
    "https://www.maths.tcd.ie/~dwilkins/Courses/MA232A/Euclid_ETexts/"
    "Euclid_BookI__MultiAuthor__Propositions.html"
)
PDF_BASE = (
    "http://www.maths.tcd.ie/~dwilkins/Courses/MA232A/MA232A_Euclid_TLHeath_Propositions/"
)
PDF_BOOKS = {"II": "EuclidBookIIPropositions.pdf", "III": "EuclidBookIIIPropositions.pdf",
             "IV": "EuclidBookIVPropositions.pdf"}

BOOK_ORDER = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]

# TeX's OT1 encoding puts ligatures in the control-character range.
OT1_LIGATURES = {
    "\x0b": "ff", "\x0c": "fi", "\x0d": "fl", "\x0e": "ffi", "\x0f": "ffl",
    "\x10": "i", "\x11": "j", "\x19": "ss",
}

# A TJ adjustment more negative than this is a word gap rather than kerning.
WORD_GAP = 100


def download(url: str, name: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if path.exists():
        return path.read_bytes()
    request = urllib.request.Request(
        url, headers={"User-Agent": "executable-euclid/0.1 (+https://github.com/)"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    path.write_bytes(data)
    return data


# ---------------------------------------------------------------------------
# Book I, from HTML
# ---------------------------------------------------------------------------


def _clean_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment).replace("\xa0", " ")
    return re.sub(r"\s+", " ", fragment).strip()


def parse_book_one(page: str) -> dict[str, str]:
    found: dict[str, str] = {}
    pattern = re.compile(
        r'<div class="eustatement" id="EuclidBookIProp(\d+)Statement_Heath1908">(.*?)</div>',
        re.S,
    )
    for match in pattern.finditer(page):
        paragraphs = re.findall(r"<p>(.*?)</p>", match.group(2), re.S)
        text = " ".join(_clean_html(part) for part in paragraphs).strip()
        if text:
            found[f"I.{int(match.group(1))}"] = text
    return found


# ---------------------------------------------------------------------------
# Books II-IV, from PDF
# ---------------------------------------------------------------------------


def _decode_pdf_string(raw: bytes) -> str:
    def unescape(match: re.Match) -> bytes:
        body = match.group(1)
        if body.isdigit():
            return bytes([int(body, 8)])
        return {b"n": b"\n", b"t": b"\t", b"r": b"\r"}.get(body, body)

    text = re.sub(rb"\\([0-7]{1,3}|.)", unescape, raw).decode("latin-1")
    for glyph, letters in OT1_LIGATURES.items():
        text = text.replace(glyph, letters)
    return text


def extract_pdf_text(pdf: bytes) -> str:
    """Recover readable text from a TeX-produced PDF, spaces and all."""
    pieces: list[str] = []
    for stream in re.finditer(rb"stream\r?\n(.*?)endstream", pdf, re.S):
        try:
            content = zlib.decompress(stream.group(1))
        except zlib.error:
            continue
        for array in re.finditer(rb"\[(.*?)\]\s*TJ", content, re.S):
            line: list[str] = []
            for token in re.finditer(rb"\((?:\\.|[^\\()])*\)|-?\d+(?:\.\d+)?", array.group(1)):
                chunk = token.group(0)
                if chunk.startswith(b"("):
                    line.append(_decode_pdf_string(chunk[1:-1]))
                elif float(chunk) <= -WORD_GAP:
                    line.append(" ")
            pieces.append("".join(line))
        for single in re.finditer(rb"\((?:\\.|[^\\()])*\)\s*Tj", content, re.S):
            pieces.append(_decode_pdf_string(single.group(0).rsplit(b")", 1)[0][1:]))
    return "\n".join(pieces)


def parse_pdf_book(text: str, book: str) -> dict[str, str]:
    """Take the enunciation following each ``Proposition N`` heading."""
    found: dict[str, str] = {}
    pattern = re.compile(r"Proposition\s+(\d+)\s*(.*?)(?=Proposition\s+\d+|\Z)", re.S)
    for match in pattern.finditer(text):
        number = int(match.group(1))
        body = re.sub(r"\s+", " ", match.group(2)).strip()
        sentence = _first_sentence(body)
        if sentence and len(sentence) > 25:
            found.setdefault(f"{book}.{number}", sentence)
    return found


def _first_sentence(text: str) -> str:
    """Heath's enunciations are a single sentence; the proof begins after it."""
    # Rejoin words the typesetter broke across lines. A real compound keeps its
    # hyphen tight ("right-angled"), so only "x- y" is an artefact.
    text = re.sub(r"([a-z])- ([a-z])", r"\1\2", text)
    match = re.search(r"^(.+?\.)(?:\s|$)", text)
    return match.group(1).strip() if match else ""


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
    return ""


def main() -> int:
    statements: dict[str, str] = {}

    print(f"Book I  <- {BOOK_ONE}")
    page = download(BOOK_ONE, "EuclidBookI_Heath1908.html").decode("utf-8", "replace")
    statements.update(parse_book_one(page))
    print(f"         {len([r for r in statements if r.startswith('I.')])} enunciations")

    for book, name in PDF_BOOKS.items():
        try:
            pdf = download(PDF_BASE + name, name)
        except Exception as exc:  # pragma: no cover - network trouble
            print(f"Book {book} <- skipped ({exc})", file=sys.stderr)
            continue
        parsed = parse_pdf_book(extract_pdf_text(pdf), book)
        statements.update(parsed)
        print(f"Book {book:<3} <- {name}: {len(parsed)} enunciations")

    complaints = {ref: why for ref, why in
                  ((ref, suspicious(ref, text)) for ref, text in statements.items()) if why}
    for ref, why in sorted(complaints.items()):
        print(f"  DROPPED {ref}: {why}", file=sys.stderr)
    for ref in complaints:
        del statements[ref]

    missing = [f"I.{n}" for n in range(1, 49) if f"I.{n}" not in statements]
    if missing:
        print(f"  WARNING: Book I is incomplete: {', '.join(missing)}", file=sys.stderr)

    payload = {
        "translation": "Thomas L. Heath, The Thirteen Books of Euclid's Elements "
        "(Cambridge University Press, 1908). Public domain.",
        "transcription": "D. R. Wilkins, Trinity College Dublin.",
        "sources": [BOOK_ONE] + [PDF_BASE + name for name in PDF_BOOKS.values()],
        "note": "Downloaded and parsed, not retyped. Propositions absent here fall "
        "back to the editorial summaries carried in the code, and every display "
        "of a statement reports which it is showing.",
        "statements": dict(sorted(statements.items(), key=_sort_key)),
    }
    DESTINATION.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {len(statements)} statements to {DESTINATION.relative_to(ROOT)}")
    return 0


def _sort_key(item: tuple[str, str]) -> tuple[int, int]:
    book, number = item[0].split(".")
    return (BOOK_ORDER.index(book) if book in BOOK_ORDER else 99), int(number)


if __name__ == "__main__":
    raise SystemExit(main())
