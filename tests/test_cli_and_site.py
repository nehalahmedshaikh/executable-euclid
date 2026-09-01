"""The command line and the generated site."""

import collections
import html
import inspect
import random
import re
from pathlib import Path

import pytest

import euclid.elements  # noqa: F401  -- registers the propositions
from euclid.cli import main
from euclid.elements.registry import (
    ERRATA,
    HEATH,
    Proposition,
    all_propositions,
    get,
    proposition,
    run_sampled,
)
from euclid.plane.objects import Point
from euclid.plane.predicates import on_circle, on_line
from euclid.render.site import _legibility, _sample_trace
from euclid.render.svg import _collect, _the_propositions_own, render_trace
from euclid.verify.ledger import audit


def test_classify_from_the_command_line(capsys):
    assert main(["classify", "sqrt(3)+sqrt(5)"]) == 0
    assert "sixth binomial" in capsys.readouterr().out


def test_classify_rejects_inexact_input(capsys):
    assert main(["classify", "1.414"]) == 1
    assert "exact" in capsys.readouterr().err


def test_ngon(capsys):
    assert main(["ngon", "17"]) == 0
    assert "constructible" in capsys.readouterr().out
    assert main(["ngon", "7"]) == 0
    output = capsys.readouterr().out
    assert "impossible" in output and "Fermat" in output


def test_impossible(capsys):
    assert main(["impossible"]) == 0
    output = capsys.readouterr().out
    assert output.count("impossible") == 3
    assert "degree 3" in output


def test_run_and_why(capsys):
    assert main(["run", "I.47"]) == 0
    assert "verified exactly" in capsys.readouterr().out
    assert main(["why", "I.47"]) == 0
    output = capsys.readouterr().out
    assert "parallel postulate: required" in output


def test_minimal(capsys):
    assert main(["minimal", "I.47"]) == 0
    output = capsys.readouterr().out
    assert "minimal Elements for I.47" in output
    assert "I.1" in output


def test_unknown_proposition_is_an_error(capsys):
    assert main(["why", "I.99"]) == 1


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    """The generated site, built once and shared by every test that reads it.

    Building it costs about as much as the whole of the rest of the suite, and
    the cost grows with every proposition added, so it is not done nine times
    over. The one test that changes what the site would contain builds its own.
    """
    out = tmp_path_factory.mktemp("site")
    assert main(["site", "--out", str(out), "--no-search"]) == 0
    return out


def test_site_builds_without_broken_links(site):
    pages = sorted(site.glob("*.html"))
    assert len(pages) > 70

    names = {page.name for page in pages}
    broken = set()
    for page in pages:
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.endswith(".html") and href not in names:
                broken.add((page.name, href))
    assert not broken, f"broken links: {sorted(broken)[:5]}"


def test_every_geometric_proposition_gets_a_diagram(site):
    for ref in ("I-1", "I-47", "IV-11", "II-11"):
        page = (site / f"{ref}.html").read_text(encoding="utf-8")
        assert "<svg" in page, f"{ref} has no figure"
        assert 'class="figure"' in page


@pytest.fixture(scope="session")
def drawn_figures():
    """Every proposition that draws anything, with what it drew.

    Choosing a figure means sampling many configurations and scoring them, so
    it is done once and shared rather than by each test in turn.
    """
    figures = []
    for entry in all_propositions():
        trace = _sample_trace(entry)
        if trace is None:
            continue
        points, lines, circles = _collect(trace)
        if not lines and not circles:
            continue  # Books V and VII-IX argue about magnitudes, not figures
        figures.append((entry, trace, points, lines, circles))
    return figures


def test_no_point_is_drawn_with_nothing_joined_to_it(drawn_figures):
    """A point floating free means the figure is missing something.

    This is the shape of every figure bug found so far, and all of them were
    found by eye: I.1 not drawing the given line its whole construction rests
    on, I.23 not drawing the arms of the given angle, III.31 arguing about a
    circle it never drew. In each case the give-away was a lettered point with
    nothing attached to it. Checking it costs nothing and does not need eyes.

    Only the proposition's own points count -- an inherited scaffolding point is
    drawn faint and unlettered, and is nobody's subject.
    """
    for entry, trace, points, lines, circles in drawn_figures:
        own, _ = _the_propositions_own(trace)
        centres = {circle.centre for circle in circles}
        adrift = [
            point.label or repr(point)
            for point in points
            if point in own
            and point not in centres
            and not any(on_line(point, line) for line in lines)
            and not any(on_circle(point, circle) for circle in circles)
        ]
        assert not adrift, f"{entry.ref} draws {adrift} joined to nothing"


def test_every_geometric_proposition_draws_more_than_a_dot(drawn_figures):
    """A figure has to be a figure."""
    for entry, trace, points, lines, circles in drawn_figures:
        assert len(lines) + len(circles) >= 2, f"{entry.ref} draws too little to read"
        assert len(points) >= 2, entry.ref


def test_the_chosen_figures_are_legible(drawn_figures):
    """The one shown on the page is picked for clarity from many valid ones.

    Not a claim about the mathematics -- verification samples widely on purpose,
    and an awkward configuration is a better test. This only guards the picture.
    """
    for entry, trace, points, lines, circles in drawn_figures:
        assert _legibility(trace) > 0.35, f"{entry.ref} is drawn too cramped to read"


def test_no_figure_letters_a_point_twice(drawn_figures):
    """One letter, one point.

    Nested propositions letter their own parameters, so the same letter can be
    claimed by two different places in one figure -- I.47 once showed four
    points called C. The renderer keeps the first claim and leaves the rest as
    bare dots.
    """
    for entry, trace, _, _, _ in drawn_figures:
        figure = render_trace(trace, entry.ref)
        letters = re.findall(r'class="letter">(\w+)</text>', figure)
        assert len(letters) == len(set(letters)), f"{entry.ref} letters a point twice: {letters}"


def test_a_figure_separates_its_own_work_from_its_helpers(drawn_figures):
    """The subject is drawn firm, the apparatus that found it is drawn back.

    A figure-level move fans out to every enclosing trace, so a proposition
    standing on helpers inherits nearly everything drawn -- I.3 draws eight of
    the twenty-six objects in its own figure. At one weight the subject is lost.
    """
    standing_alone = standing_on_helpers = 0
    for entry, trace, _, lines, _ in drawn_figures:
        if not lines:
            continue  # the arithmetic books draw nothing
        figure = render_trace(trace, entry.ref)
        if trace.descendants():
            standing_on_helpers += 1
        else:
            standing_alone += 1
            assert "aside" not in figure, f"{entry.ref} has no helpers, so nothing to hold back"
    assert standing_alone and standing_on_helpers, "expected both kinds of figure"

    # I.3 stands on I.2, which stands on I.1.
    nested = render_trace(_sample_trace(get("I.3")), "I.3")
    assert nested.count('class="ray aside"') > nested.count('class="ray"/')


def test_marking_a_result_overrides_ownership():
    """The one case ownership cannot get right.

    I.44's answer is a parallelogram that I.42 built, so by ownership it would
    be held back along with the rest of the apparatus. Saying so explicitly is
    what `result()` is for, and it wins.
    """
    for ref in ("I.44", "I.45"):
        trace = run_sampled(ref, random.Random(7)).trace
        figure = render_trace(trace, ref)
        assert trace.results, f"{ref} marks no result"
        assert figure.count('class="ray aside"') > figure.count('class="ray"/'), ref
        assert len(re.findall(r'class="letter"', figure)) <= 10, ref
        # the marked answer is drawn firm even though a helper made it
        answer = [item for item in trace.results if not isinstance(item, Point)]
        assert answer, ref


def test_the_index_reports_real_numbers(site):
    index = (site / "index.html").read_text(encoding="utf-8")
    stats = dict(
        (label, int(value))
        for value, label in re.findall(r"<b>(\d+)</b><span>([^<]+)</span>", index)
    )
    assert stats["propositions"] == len(all_propositions())
    assert stats["steps checked"] > 500
    assert stats["unproved assumptions"] > 0


def test_the_readme_numbers_are_current():
    """The README quotes counts that go stale every time a book grows.

    They have gone stale twice and been corrected by hand both times, which is
    what a test is for. Every number below is read straight out of the registry.
    """
    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
    entries = all_propositions()

    headline = re.search(r"\*\*(\d+) propositions\*\*, [\d,]+ checked steps", readme)
    assert headline, "the README no longer states a proposition count"
    assert int(headline.group(1)) == len(entries)

    assert f"**{len(HEATH)} enunciations**" in readme, "the enunciation count is stale"

    # The coverage table: one row per book, "encoded / total".
    counted = collections.Counter(entry.book for entry in entries)
    rows = re.findall(r"^\| \*{0,2}([IVX]+)\*{0,2} \| \*{0,2}(\d+) / (\d+)", readme, re.M)
    assert len(rows) == 13, f"expected a row per book, found {len(rows)}"
    for book, encoded, total in rows:
        assert int(encoded) == counted[book], f"Book {book}: README says {encoded}"


def test_every_statement_is_heath_word_for_word(site):
    """No page may show anything but the parsed text, verbatim."""
    for entry in all_propositions():
        page = (site / f"{entry.ref.replace('.', '-')}.html").read_text(encoding="utf-8")
        assert "Heath, 1908" in page, entry.ref
        assert entry.statement == HEATH[entry.ref]
        assert html.escape(entry.statement, quote=False) in page, entry.ref


def test_a_proposition_cannot_carry_its_own_wording():
    """Hard rule: statements are parsed, never written.

    The decorator has no parameter for what a proposition says, and the lookup
    raises rather than inventing a stand-in, so there is no route by which a
    paraphrase could reach a page.
    """
    assert "title" not in inspect.signature(proposition).parameters

    orphan = Proposition(ref="I.99", book="I", number=99, kind="theorem", raw=lambda: None)
    with pytest.raises(KeyError, match="parsed, never written"):
        orphan.statement

    with pytest.raises(KeyError, match="not a proposition of the Elements"):
        proposition("XIV.1")(lambda: None)


def test_the_errata_are_published_in_full(site):
    """Every departure from the scan is listed where a reader can check it."""
    page = (site / "text.html").read_text(encoding="utf-8")
    assert ERRATA, "the errata block is missing from heath.json"
    for item in ERRATA:
        assert item["ref"] in page
        assert item["source_reads"] in page
        assert item["corrected_to"] in page
        # and the correction really is in the shipped text
        assert item["corrected_to"] in HEATH[item["ref"]]
        if item["source_reads"] not in item["corrected_to"]:
            # a substitution, so the misprint must be gone; an addition (a lost
            # full stop) leaves the original reading as a prefix of the fix
            assert item["source_reads"] not in HEATH[item["ref"]]


def test_the_findings_page_reports_the_real_results(site):
    """Every finding is measured, labelled by strength, and reproducible.

    This used to require the words "parallel postulate", which was the page's
    worst overclaim: that finding is somebody typing ``"Post.5"`` beside I.29 and
    not beside I.27, and only 12% of the graph's edges are executed at all. The
    requirement is now the opposite one.
    """
    findings = (site / "findings.html").read_text(encoding="utf-8")

    for banished in ("parallel postulate", "Postulate 5", "depend on I.1",
                     "holds up the whole book", "a quarter of what has been written"):
        assert banished not in findings, f"{banished!r} is derived from citations"

    # What is left, and the kind of claim each one is.
    for expected in ("Exhaustive", "Measured", "Empirical",
                     "II.9 and II.10", "Book X", "coverage"):
        assert expected in findings, expected

    # This site is built with --no-search, so the shortest-construction results
    # were never computed for it -- and the page must therefore not state them.
    # The old page carried "exactly seven circles" as prose no matter what the
    # build had actually run, which is the failing the rewrite is about.
    assert "seven circles" not in findings

    # Nothing may sit here without the command that reproduces it.
    assert findings.count("<pre>euclid ") >= findings.count('<div class="finding">') - 1


def test_the_pages_agree_with_each_other(site):
    """The same quantity must not be computed twice and reported differently.

    It was. ``build`` audited each proposition at ``trials=3`` for the headline
    figure while the ledger page audited at ``trials=8`` for its own, so one
    build shipped an index saying 355 unproved assumptions and a ledger page
    saying 350. Nobody compared the two pages. This does.
    """
    numbers = {}
    for page in ("index.html", "findings.html", "ledger.html"):
        text = (site / page).read_text(encoding="utf-8")
        found = re.search(r"<b>(\d+)</b><span>(?:unproved assumptions|points assumed"
                          r" to exist)</span>", text)
        if found:
            numbers[page] = int(found.group(1))
    found = re.search(r"<strong>(\d+) places</strong>",
                      (site / "findings.html").read_text(encoding="utf-8"))
    if found:
        numbers["findings.html/prose"] = int(found.group(1))
    assert len(set(numbers.values())) == 1, numbers


def test_no_page_claims_every_proof_is_case_independent(site):
    """Four propositions do vary by figure, and every page must say so.

    The ledger page counted them in its own table while the findings page said
    "There are none" and the ledger prose said "The column is empty". All three
    were generated from the same build.
    """
    # Read the refs off the page, then re-derive the verdict for those and for
    # controls. Auditing all 390 again here cost five and a half minutes and
    # duplicated exactly what the build that made this site had just done.
    ledger_page = (site / "ledger.html").read_text(encoding="utf-8")
    section = ledger_page.split("Steps that vary by figure")[1].split("</p>")[0]
    varying = re.findall(r'href="([IVX]+)-(\d+)\.html"', section)
    varying = [f"{book}.{number}" for book, number in varying]
    assert varying, "the case detector found nothing; this test is now vacuous"

    for ref in varying:
        assert audit(ref, trials=8).of_kind("case"), f"{ref} is named but does not vary"
    controls = ["I.1", "I.47", "III.1", "VI.1"]
    for ref in controls:
        assert not audit(ref, trials=8).of_kind("case"), f"{ref} varies but is not named"

    for page in ("findings.html", "ledger.html"):
        text = (site / page).read_text(encoding="utf-8")
        assert "There are none" not in text
        assert "The column is empty" not in text
        for ref in varying:
            assert ref in text, f"{page} does not name {ref}"

    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(
        encoding="utf-8"
    )
    assert "There are none" not in readme


def test_the_site_uses_exactly_three_colours(site):
    """Black, white, and one grey exactly halfway between. Nothing else."""
    found = set()
    for page in list(site.glob("*.html")) + [site / "style.css"]:
        found |= set(re.findall(r"#([0-9a-fA-F]{6})", page.read_text(encoding="utf-8")))
    assert {value.lower() for value in found} == {"000000", "808080", "ffffff"}


def test_the_site_never_fakes_a_fourth_shade(site):
    """Opacity or alpha would manufacture greys outside the palette."""
    style = (site / "style.css").read_text(encoding="utf-8")
    assert "opacity" not in style
    assert "rgba" not in style


def test_the_stylesheet_is_shared_rather_than_inlined(site):
    """It used to be inlined into all 398 pages: 61% of everything shipped.

    Worse than the bytes, a one-line CSS change rewrote every file in docs/, so
    the git history carried a full copy of the site per tweak.
    """
    css = site / "style.css"
    assert css.exists()
    for page in site.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        assert '<link rel="stylesheet" href="style.css">' in text, page.name
        assert "<style>" not in text, f"{page.name} still inlines CSS"


def test_the_stylesheet_parses(site):
    """Braces and comments balance, and no rule is stranded outside a block.

    An edit once closed a comment twice, leaving prose where a selector should
    be. Everything up to the next brace became part of that selector, so the
    rule after it -- the one making the graph scrollable -- was silently
    dropped. Nothing failed; the page just quietly lost a feature.
    """
    css = (site / "style.css").read_text(encoding="utf-8")
    assert css.count("{") == css.count("}"), "unbalanced braces"
    assert css.count("/*") == css.count("*/"), "unbalanced comments"

    stripped = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for chunk in re.findall(r"(^|\})([^{}]*)\{", stripped, flags=re.M):
        selector = chunk[1].strip()
        assert selector, "empty selector"
        # A real selector is punctuated -- dots, colons, commas, hashes. A run
        # of four bare lowercase words in a row is a sentence that escaped its
        # comment. ("nav.top a" has one such word and is fine.)
        words = [token for token in selector.split() if re.fullmatch(r"[a-z]+", token)]
        assert len(words) < 4, (
            f"this looks like prose, not a selector: {selector[:70]!r}"
        )


def test_theorems_draw_the_figures_they_argue_about(site):
    """A proposition handed a triangle should still show you the triangle."""
    for ref in ("I-41", "I-4", "I-37", "I-20", "VI-4"):
        page = (site / f"{ref}.html").read_text(encoding="utf-8")
        assert page.count("<line ") >= 3, f"{ref} renders as bare dots"


def test_numbers_written_into_prose_match_their_source(site):
    """A figure typed into a sentence goes stale silently.

    Most numbers on these pages are interpolated from a measurement. These are
    not -- they are spelled out because the sentence reads better that way --
    so each is tied back to the constant it describes. Changing the constant
    now breaks a test instead of leaving the page quietly wrong.
    """
    from euclid.elements.samples import AWKWARD_IN
    from euclid.measure.gaps import COEFFICIENT, SQUAREFREE
    from euclid.search.optimizer import DEFAULT_MAX_POINTS
    from euclid.search.state import EPSILON

    # The construction rows are recorded, and this site is built with
    # --no-search, so they appear only where the index states them in words.
    everything = "".join((site / name).read_text(encoding="utf-8") for name in
                         ("index.html", "findings.html", "optimizer.html", "graph.html"))

    assert AWKWARD_IN == 6, "the findings page says one draw in six"
    assert DEFAULT_MAX_POINTS == 20, "the optimizer page says more than twenty points"
    assert COEFFICIENT == 2, "the Book X finding says coefficients up to 2"
    assert max(SQUAREFREE) == 11, "the Book X finding says squarefree up to 11"
    assert EPSILON == 1e-9, "the optimizer page says a tangency lost at 10^-9"

    from euclid.graph.dag import build as build_graph

    executed, cited = build_graph().provenance()
    share = executed / (executed + cited)
    assert 0.11 <= share <= 0.14, (
        f"the footer says about one edge in eight; it is {share:.1%}")

    # The compass-only result is stated in words on two pages and must track
    # what was actually enumerated.
    from euclid.measure import load_findings

    rows = {(r["problem"], r["isa"]): r for r in load_findings()["constructions"]}
    if ("midpoint", "compass-only") in rows:
        length = rows[("midpoint", "compass-only")]["length"]
        assert length == 6 and "six circles" in everything
        assert "seven circles" not in everything
