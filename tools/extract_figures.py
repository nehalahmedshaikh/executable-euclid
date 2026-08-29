"""Pull Heath's own diagrams out of the source, to check ours against.

Every figure on the site is drawn from a construction that ran, so a figure can
be *exactly right* and still not be the figure Euclid drew -- lettered
differently, oriented differently, or drawing the same theorem about a different
case.  Nothing in the test suite can see that.  A person can, in a second, if
the two pictures are side by side.

So this writes Heath's diagram for each proposition next to ours, and an HTML
page laying them out in pairs.

Only Books I and II can be compared, and that is a limit of this source rather
than of Euclid.  Heath prints figures throughout -- Book III is nothing but
circle diagrams -- but this edition carries them only for Books I (48) and II
(14).  Its remaining images are cover art, the Delphi catalogue, the *Data*,
the *Optics*, and the Greek text of Book I; none illustrate Books III to XIII.
Comparing a later book against a printed figure would need a different source.

Output goes to ``tools/sources/figures/``, inside the gitignored download cache:
these are reference material for looking at, not something the repository ships.
Heath's 1908 diagrams are themselves public domain, but they are not needed at
run time and there is no reason to carry them.

Run with ``python tools/extract_figures.py``.
"""

from __future__ import annotations

import random
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_heath import CACHE, EPUB_BOOKS, EPUB_HEADING, EPUB_NAME  # noqa: E402

DESTINATION = CACHE / "figures"

# Only these documents carry proposition diagrams; the others in the epub
# illustrate the introduction and Euclid's other works.
ILLUSTRATED = ("I", "II")

MARKER = re.compile(
    r'PROPOSITION\s+(?:[IVXL]+|\d+)\s*\.?\s*</span>|<img[^>]*src="images/([^"]+)"',
    re.I,
)


def figures_by_proposition(archive: zipfile.ZipFile) -> dict[str, str]:
    """Map each proposition to the image that follows its heading."""
    found: dict[str, str] = {}
    for book in ILLUSTRATED:
        for name, first in EPUB_BOOKS[book]:
            document = archive.read(f"Ops/{name}").decode("utf-8", "replace")
            number = first - 1
            for match in MARKER.finditer(document):
                image = match.group(1)
                if image is None:  # a heading: the next image belongs to it
                    number += 1
                elif f"{book}.{number}" not in found and number >= first:
                    found[f"{book}.{number}"] = image
    return found


def our_figure(ref: str) -> str:
    """The diagram this project draws for the same proposition."""
    from euclid.elements import registry
    from euclid.render.svg import render_trace

    import euclid.elements  # noqa: F401  -- registers the propositions

    for seed in range(12):
        try:
            run = registry.run_sampled(ref, random.Random(f"site:{ref}:3" if seed == 0 else seed))
        except Exception:
            continue
        return render_trace(run.trace, ref)
    return "<p>no figure</p>"


def comparison_page(pairs: list[tuple[str, str, str]]) -> str:
    rows = "".join(
        f"<tr><th>{ref}</th>"
        f'<td><img src="{image}" alt="Heath {ref}"></td>'
        f"<td>{drawn}</td></tr>"
        for ref, image, drawn in pairs
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Heath's figures against ours</title><style>"
        "body{background:#fff;color:#000;font:15px/1.6 Georgia,serif;margin:2rem auto;"
        "max-width:1100px}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border-bottom:1px solid #808080;padding:1rem;vertical-align:middle;"
        "text-align:center}"
        "th{width:70px;font:600 13px ui-monospace,monospace}"
        "td{width:50%}img{max-width:100%;height:auto}"
        "svg.figure{max-width:100%;height:auto;border:1px solid #808080}"
        "svg.figure .arc{stroke:#808080;stroke-width:1;stroke-dasharray:3 3}"
        "svg.figure .ray{stroke:#000;stroke-width:1.4}"
        "svg.figure .ray.aside{stroke:#808080;stroke-width:.7}"
        "svg.figure .arc.aside{stroke:#808080;stroke-width:.6;stroke-dasharray:2 4}"
        "svg.figure .dot{fill:#000}svg.figure .dot.aside{fill:#808080}"
        "svg.figure .letter{fill:#000;font:italic 14px Georgia,serif}"
        "caption{text-align:left;padding-bottom:1rem}"
        "</style></head><body>"
        "<h1>Heath's figures against ours</h1>"
        "<p><b>This is a bug-finder, not a scorecard.</b> The two columns are different "
        "kinds of thing and will not match. Heath's figure is <em>composed</em>: he picks "
        "a configuration that shows the case well, draws the arcs the argument needs, and "
        "letters to suit. Ours is a <em>trace</em>: sampled coordinates, whatever objects "
        "the code made, lettering from the parameter names. Reading down the columns "
        "looking for resemblance is not the use of this page.</p>"
        "<p>Expect all of these, and do not report them:</p>"
        "<ul>"
        "<li><b>Different shape and lettering</b> &mdash; ours is sampled, not chosen.</li>"
        "<li><b>Fewer auxiliary points</b> &mdash; Euclid needs a construction to "
        "<em>argue</em> steps the exact arithmetic settles outright.</li>"
        "<li><b>No impossible configurations</b> &mdash; where he argues by contradiction "
        "his figure shows the case being refuted. I.7 draws two distinct apexes over one "
        "base; that configuration does not exist, so it cannot be built here. Ours shows "
        "them coincident, because the claim proves they are.</li>"
        "</ul>"
        "<p><b>Worth reporting:</b> a construction line that a cited step depends on and "
        "ours omits &mdash; this page caught exactly that in II.4, where I.43 was cited "
        "for the complements about a diameter that was never drawn. Also: a point with "
        "nothing joined to it, or a figure showing a different <em>case</em> of the "
        "proposition than the one argued.</p>"
        f"<table><tr><th></th><th>Heath, 1908</th><th>Drawn here</th></tr>{rows}</table>"
        "</body></html>"
    )


def main() -> int:
    epub = CACHE / EPUB_NAME
    if not epub.exists():
        print(f"no source: put the epub at {epub.relative_to(ROOT)}", file=sys.stderr)
        return 1

    DESTINATION.mkdir(parents=True, exist_ok=True)
    pairs: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(epub) as archive:
        mapping = figures_by_proposition(archive)
        for ref, image in sorted(mapping.items(), key=lambda item: (
                item[0].split(".")[0], int(item[0].split(".")[1]))):
            suffix = Path(image).suffix
            name = f"{ref.replace('.', '-')}{suffix}"
            (DESTINATION / name).write_bytes(archive.read(f"Ops/images/{image}"))
            pairs.append((ref, name, our_figure(ref)))

    (DESTINATION / "compare.html").write_text(comparison_page(pairs), encoding="utf-8")
    print(f"wrote {len(pairs)} figures to {DESTINATION.relative_to(ROOT)}")
    print(f"open {(DESTINATION / 'compare.html').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
