"""One function per page of the site.

Each takes what it needs already measured and returns HTML. Nothing
here computes a finding: the numbers arrive from findings.json or
from the graph, and a page that wanted to derive one would be
reporting our own transcription back.
"""

from __future__ import annotations

import html
from fractions import Fraction
from typing import Optional
from ..elements.registry import (
    BOOK_ORDER,
    BOOK_TITLES,
    ERRATA,
    HEATH,
    HEATH_CREDIT,
    Proposition,
    all_propositions,
    reference_kind,
)
from ..kernel.field import Context, fmt, sqrt, to_float
from ..plane.trace import Trace
from ..verify.ledger import audit
from .layout import graph_svg
from .svg import render_trace
from .style import _esc, _page, _slug


def _proposition_page(entry: Proposition, graph, trace: Optional[Trace],
                      ledger=None) -> str:
    body = [
        f'<p class="kicker">Book {entry.book} &middot; Proposition {entry.number}</p>',
        f"<h1>{entry.ref}</h1>",
        f"<blockquote>{_esc(entry.statement)}"
        f'<span class="src">Heath, 1908</span></blockquote>',
    ]
    corrected = [item for item in ERRATA if item["ref"] == entry.ref]
    for item in corrected:
        body.append(
            f'<p class="note">The source used here misprints this enunciation &mdash; '
            f'it reads &ldquo;{_esc(item["source_reads"])}&rdquo; where Heath has '
            f'&ldquo;{_esc(item["corrected_to"])}&rdquo; ({_esc(item["note"])}). '
            f'<a href="text.html">The full errata &rarr;</a></p>'
        )
    if entry.note:
        body.append(f'<p class="note">{_esc(entry.note)}</p>')

    if trace is not None:
        figure = render_trace(trace, entry.ref)
        if figure:
            helpers = len(trace.descendants())
            aside = (
                f", of which {helpers} helper construction{'s' if helpers > 1 else ''} "
                "drew the fainter ones"
                if helpers
                else ""
            )
            body.append(
                f"<figure>{figure}<figcaption>"
                f"{trace.step_count} lines and circles drawn{aside}"
                "</figcaption></figure>"
            )

    if trace is not None and trace.claims:
        body.append("<h2>Every step, checked</h2><ul class=\"claims\">")
        for item in trace.claims:
            given = item.by == ("hypothesis",)
            citations = ", ".join(
                f'<a href="{_slug(ref)}.html">{ref}</a>'
                if reference_kind(ref) == "proposition" and ref in graph.nodes
                else _esc(ref)
                for ref in item.by
            )
            body.append(
                f'<li class="{"hyp" if given else ""}">{_esc(item.text)}'
                f'<span class="cite">{"given" if given else f"by {citations}"}</span></li>'
            )
        body.append("</ul>")

    needs = sorted(graph.needs(entry.ref), key=lambda r: graph.nodes[r].sort_key())
    used_by = sorted(graph.dependents(entry.ref), key=lambda r: graph.nodes[r].sort_key())
    uncoded = sorted(entry.depends_on - set(graph.nodes))
    body.append("<h2>What it needs, and what needs it</h2>")
    if needs:
        links = " ".join(f'<a href="{_slug(r)}.html">{r}</a>' for r in needs)
        body.append(f"<p><strong>Needs:</strong> {links}</p>")
    else:
        body.append("<p><strong>Needs:</strong> nothing earlier.</p>")
    if used_by:
        links = " ".join(f'<a href="{_slug(r)}.html">{r}</a>' for r in used_by)
        body.append(f"<p><strong>Used by:</strong> {links}</p>")
    if uncoded:
        body.append(
            f'<p class="note"><strong>Also cites</strong> {", ".join(uncoded)}, which '
            "this project has not written out yet.</p>"
        )
    axioms = sorted(graph.axioms(entry.ref))
    if axioms:
        body.append(f"<p><strong>Rests on:</strong> {', '.join(axioms)}</p>")
    body.append(
        f"<p><strong>Depth:</strong> {graph.depth(entry.ref)} steps of argument above the "
        "first principles. <strong>Parallel postulate:</strong> "
        f"{'needed' if graph.uses_parallel_postulate(entry.ref) else 'not needed'}.</p>"
    )

    # Handed in by build(), which audits every proposition once. This used to
    # audit again at trials=6 while the ledger page audited at trials=8, so the
    # corpus was walked twice for the same answer.
    if ledger is None:
        ledger = audit(entry.ref, trials=8)
    body.append("<h2>What it takes on trust</h2>")
    if ledger.is_clean:
        body.append('<p class="note">Nothing. It draws no intersections and reads '
                    "nothing off the picture.</p>")
    else:
        body.append('<ul class="claims">')
        for item in ledger.assumptions:
            times = f" (&times;{item.occurrences})" if item.occurrences > 1 else ""
            body.append(
                f'<li>{_esc(item.detail)}{times}<span class="cite">{item.kind}</span></li>'
            )
        body.append("</ul>")

    source = entry.source()
    if source:
        body.append(f"<h2>The proposition as code</h2><pre>{_esc(source)}</pre>")

    return _page(f"{entry.ref} — Executable Euclid", "".join(body))


def _index_page(graph, stats) -> str:
    top_ref, top_count = graph.load_bearing()[0]
    body = [
        '<p class="kicker">Euclid\'s Elements, as software</p>',
        "<h1>Executable Euclid</h1>",
        '<p class="lede">Every proposition is a small program. It draws its own figure '
        "with a straightedge and compass, checks its own conclusion, and says what it "
        "depended on. Nothing is measured or approximated.</p>",
        '<div class="stat">',
        f"<div><b>{len(graph.nodes)}</b><span>propositions</span></div>",
        f"<div><b>{stats['claims']}</b><span>steps checked</span></div>",
        f"<div><b>{stats['edges']}</b><span>dependency edges</span></div>",
        f"<div><b>{stats['continuity']}</b><span>unproved assumptions</span></div>",
        "</div>",
        "<h2>The idea</h2>",
        "<p>A straightedge and compass can only produce certain numbers: the ones you "
        "reach from whole numbers by adding, subtracting, multiplying, dividing, and "
        "taking square roots. This project stores those numbers exactly, as square roots "
        "piled on square roots, never as decimals.</p>",
        "<p>That sounds like a small choice, but it changes what the machine can say. "
        "Two lengths are either equal or they are not; there is no rounding, no tolerance "
        "to set, and no near-miss that might be mistaken for a theorem. Everything else "
        "on this site follows from that.</p>",
        "<h2>What it found</h2>",
        "<ul>",
        '<li><a href="findings.html">The book measured by algebraic depth.</a> Every '
        "magnitude a construction produces has an exact degree over the rationals, so "
        "each book has a ceiling. I.1 already needs a square root; Books VII to IX never "
        "leave the rationals; X.115 reaches degree 32.</li>",
        '<li><a href="findings.html">Hypotheses broken on purpose.</a> Move a given until '
        "one of Euclid's stated conditions fails, then run without enforcing it, and see "
        "whether the conclusion held anyway. II.9 and II.10 turn out to be the same "
        "identity written twice.</li>",
        '<li><a href="findings.html">A constructible number Book X cannot name.</a> The '
        "thirteen species do not cover everything a straightedge and compass produce, and "
        "the classifier finds the boundary.</li>",
        '<li><a href="ledger.html">The gaps Euclid never mentions.</a> His rules let you '
        "draw circles, but never say that two circles meet. He uses that fact anyway, "
        "starting on page one.</li>",
        '<li><a href="optimizer.html">The shortest possible constructions.</a> Where the '
        "table says <em>fewest possible</em>, every shorter figure was ruled out in exact "
        "arithmetic. With no straightedge at all a midpoint costs six circles.</li>",
        '<li><a href="graph.html">What depends on what.</a> Two kinds of edge, and the '
        f"page says which is which: {top_ref} carries {top_count} of the others, but most "
        "of that is Euclid's own cross-references.</li>",
        "</ul>",
        '<p><a href="findings.html"><strong>All the findings in one place &rarr;</strong>'
        "</a></p>",
        "<h2>The propositions</h2>",
    ]

    by_book: dict[str, list[Proposition]] = {}
    for entry in all_propositions():
        by_book.setdefault(entry.book, []).append(entry)
    # "(complete)" used to be hardcoded to Book I and stayed there while nine
    # more books were finished. It is counted against the text instead.
    in_heath: dict[str, int] = {}
    for ref in HEATH:
        in_heath[ref.split(".")[0]] = in_heath.get(ref.split(".")[0], 0) + 1
    for book, entries in by_book.items():
        title = BOOK_TITLES.get(book, "")
        total = in_heath.get(book, 0)
        note = " &mdash; complete" if total and len(entries) == total else (
            f" &mdash; {len(entries)} of {total}" if total else ""
        )
        body.append(f"<h3>Book {book}: {_esc(title)}{note}</h3>")
        body.append('<div class="grid">')
        for entry in entries:
            body.append(f'<a href="{_slug(entry.ref)}.html">{entry.ref}</a>')
        body.append("</div>")

    body.append(
        "<h2>What &ldquo;checked&rdquo; means here</h2>"
        "<p>Each proposition is run on many different figures that fit its assumptions, "
        "and every step is tested exactly against the figure that was built. That is a "
        "strong test, but it is a test of the pictures, not a proof in Euclid's own "
        "logic. It confirms the conclusions are true of the constructions; it does not "
        "confirm they follow by his rules of reasoning.</p>"
        "<p>The references each step cites are recorded, but the test does not rely on "
        "them. So a step with the wrong reference attached still cannot slip a false "
        "statement past.</p>"
    )
    return _page("Executable Euclid", "".join(body), here="index.html")


def _findings_page(graph, stats, search_rows) -> str:
    """Only what was computed, and only with the method that produced it.

    Findings derived from the ``cites`` annotations do not belong here. Those are
    written by hand beside each step, following Heath's marginal references, so a
    page reporting them is reporting our own typing back to us. Five such
    findings used to stand on this page and have been removed. What is left was
    either enumerated exhaustively, measured exactly by running the corpus, or
    sampled -- and each says which.
    """
    from ..measure import load_findings

    measured = load_findings()
    findings = []

    if measured:
        depth = measured["depth"]
        ceiling_rows = "".join(
            f"<tr><td>{book}</td><td>{top}</td></tr>"
            for book, top in sorted(
                depth["ceilings"].items(),
                key=lambda kv: BOOK_ORDER.index(kv[0]) if kv[0] in BOOK_ORDER else 99,
            )
        )
        first = depth["first_appearances"]
        deepest = depth["deepest"][0]
        findings.append((
            "Measured &mdash; the Elements leaves the rationals on its first page",
            "<p>Every magnitude these constructions produce is an exact element of a "
            "tower of quadratic extensions of the rationals, so it has a degree, and the "
            f"kernel can state it. Running all {measured['corpus']} propositions gives a "
            "map of the work by algebraic depth. The text cannot tell you this; it is a "
            "property of what the constructions <em>do</em>.</p>"
            "<p>The equilateral triangle of <strong>I.1</strong> already needs "
            f"&radic;3, and <strong>{_esc(first.get('4', 'I.2'))}</strong> already needs "
            "a second square root standing on the first. Yet Books III and VI &mdash; all "
            "those circles, all that similarity &mdash; never exceed degree 2, and Books "
            "VII to IX never leave the rationals at all, which is what arithmetic ought "
            "to look like. The deepest point in the whole work is "
            f"<strong>{_esc(deepest['ref'])}</strong>, at degree {deepest['degree']}.</p>"
            '<div class="scroll"><table><tr><th>Book</th><th>Highest degree reached</th>'
            f"</tr>{ceiling_rows}</table></div>"
            "<pre>euclid measure --depth</pre>",
        ))

        gaps = measured["book_x_gaps"]
        if gaps["witnesses"]:
            witness = gaps["witnesses"][0]
            findings.append((
                "Exhaustive &mdash; Book X cannot name every constructible number",
                "<p>Book X sorts the irrationals into thirteen named species, and is "
                "often described as though that were all of them. A constructible number "
                "of degree at most four lies in some <span class=\"mono\">Q(sqrt m, "
                "sqrt n)</span>, where it is <span class=\"mono\">a + b&middot;sqrt m + "
                "c&middot;sqrt n + d&middot;sqrt(mn)</span>. Taking every such number with "
                "coefficients up to 2 in size and <span class=\"mono\">m &lt; n</span> "
                "squarefree up to 11, in order of height, the simplest Euclid has no word "
                "for is</p>"
                f'<p class="mono">{_esc(witness["expression"])} &nbsp;&asymp;&nbsp; '
                f'{witness["value"]:.8f}</p>'
                "<p>It is constructible with straightedge and compass, its degree over "
                f"the rationals is {witness['degree']}, and its minimal polynomial is "
                f'<span class="mono">{_esc(witness["minimal_polynomial"])}</span>. The '
                "classifier's own reason is the whole of the explanation: "
                f"<em>{_esc(witness['reason'])}</em>. Euclid classifies what comes out of "
                "applying areas, which is sums and differences of <em>two</em> terms, so "
                "a number needing three falls outside however constructible it is. The "
                f"enumeration holds {gaps['candidates_named'] + gaps['candidates_unnamed']} "
                f"magnitudes; Book X names {gaps['candidates_named']} of them and has no "
                f"word for {gaps['candidates_unnamed']}. Height ties are broken by "
                "preferring the form written without a subtraction, and the bound is a "
                "bound: a constructible of degree 8, or one with a larger radicand, lies "
                "outside the set and is not searched.</p>"
                "<pre>euclid gap --all</pre>",
            ))

        need = measured["necessity"]
        candidates = need["candidates"]
        pair = [item for item in candidates if item["ref"] in ("II.9", "II.10")]
        if pair:
            findings.append((
                "Empirical &mdash; II.9 and II.10 are one proposition, written twice",
                "<p>Both say that the squares on the two segments of a divided line are "
                "double the square on the half together with the square on the piece "
                "between the points of section. II.9 states it for a point taken "
                "<em>between</em> the ends; II.10 for a point taken beyond them. Breaking "
                "that hypothesis and running anyway, the conclusion holds either way "
                "&mdash; in every configuration tried "
                f"({pair[0]['configurations']} of them for {_esc(pair[0]['ref'])}).</p>"
                "<p>The identity does not care where the point falls on the line. Euclid "
                "needs two propositions because he has no negative length to let one "
                "cover both cases; carried out in exact arithmetic the distinction "
                "disappears, and the hypothesis separating them does no work.</p>"
                "<pre>euclid measure --needless</pre>",
            ))

        findings.append((
            "Empirical &mdash; breaking Euclid's hypotheses on purpose",
            "<p>A proposition says nothing about the configurations its hypotheses "
            "exclude, so those are normally thrown away, and one question goes unasked: "
            "<em>would the conclusion have held anyway?</em> Lifting the exclusion makes "
            "it askable. Move one given until a hypothesis breaks, then run without "
            "enforcing it.</p>"
            f"<p>Across the corpus {need['hypotheses']} hypotheses are stated. "
            f"{need['judged']} could be broken cleanly enough to judge "
            f"({100 * need['coverage']:.0f}% coverage &mdash; a run that breaks two at "
            "once says nothing about either and is discarded). Of those, "
            f"<strong>{need['needed']}</strong> proved necessary, a claim failing the "
            f"moment they went, and {need['well_defined']} turned out to be holding the "
            "construction together, which is a weaker kind of necessity.</p>"
            f"<p>{len(candidates)} survived being broken. Those are <em>candidates</em>, "
            "not results, and the likeliest reading of one is that our claims are too "
            "weak to notice the difference. That is what happened the first time "
            "this ran: seven propositions of Book III were checking things true of any "
            "four points, circle or no circle. They were strengthened, and their "
            "hypotheses became necessary.</p>"
            "<pre>euclid measure --needless</pre>",
        ))

    findings.append((
        "Measured &mdash; Euclid uses something his own rules do not give him",
        "<p>His postulates let you draw a circle. None of them says that two circles ever "
        "cross. He needs them to cross in I.1, on the very first page, to get the top "
        "corner of his triangle &mdash; and simply takes it. The gap was not stated "
        "properly until the nineteenth century.</p>"
        "<p>Every step that uses an intersection the postulates do not license is counted "
        f"as it happens: <strong>{stats['continuity']} places</strong> across Books I to "
        'X. <a href="ledger.html">The full ledger &rarr;</a></p>'
        "<pre>euclid ledger</pre>",
    ))

    ladder = measured.get("fields") if measured else None
    if ladder and ladder["counts"].get("measuring_only"):
        counts = ladder["counts"]
        blame = {w["ref"]: w for w in ladder["witnesses"]}
        lucky = ladder["buckets"]["discharged_luckily"]
        findings.append((
            "Measured &mdash; every square root in the corpus is one of three things",
            "<p>Restricting the field a construction may build in and running the corpus "
            "again is Hilbert's method: make a model where an axiom fails and see what "
            "breaks. Over the rationals no new root is allowed at all. Over the "
            "Pythagorean field only roots of sums of two squares are, which is what a "
            "straightedge and a way to carry a segment produce &mdash; a length may be "
            "measured, two circles may not be crossed. Between the two rungs, every root "
            "the corpus takes sorts into measuring, crossing, or the proposition's own "
            "irrational subject.</p>"
            '<div class="scroll"><table><tr><th>Over Q</th><th>Propositions</th></tr>'
            f'<tr><td>complete</td><td>{counts["rational"]}</td></tr>'
            f'<tr><td>need only a length measured</td><td>{counts["measuring_only"]}</td></tr>'
            f'<tr><td>need two circles to meet</td><td>{counts["needs_continuity"]}</td></tr>'
            f'<tr><td>are about an irrational</td><td>{counts["needs_magnitude"]}</td></tr>'
            f'<tr><td>vary by configuration</td><td>{counts["configuration_dependent"]}</td></tr>'
            f'<tr><td>have no rational configuration</td><td>{counts["untestable"]}</td></tr>'
            "</table></div>"
            + (
                "<p>The two cases that show what the split is for: <strong>I.1</strong> "
                f'stops in <span class="mono">{_esc(blame["I.1"]["site"])}</span> asking '
                f'for <span class="mono">sqrt({_esc(blame["I.1"]["radicand"])})</span>, '
                "and no rung short of the full constructibles gives it. "
                "<strong>I.20</strong>, the triangle inequality, stops in "
                f'<span class="mono">{_esc(blame["I.20"]["site"])}</span> asking for '
                f'<span class="mono">sqrt({_esc(blame["I.20"]["radicand"])})</span> '
                "&mdash; and completes over the Pythagorean field, because it only ever "
                "measures. It is true in the rational plane, and it appears to fail there "
                "only because our encoding builds a root where squared lengths would "
                "do.</p>"
                if "I.1" in blame and "I.20" in blame else ""
            )
            + f"<p>{len(lucky)} propositions ({_esc(', '.join(sorted(lucky)))}) complete "
            "over the Pythagorean field while the ledger records them crossing a circle. "
            "Their samplers hand them rational triangles, so the circles meet where the "
            "configuration already was. Counting those as Pythagorean would be a finding "
            "about our test data, so they are kept apart.</p>"
            f"<p>The {counts['untestable']} untestable propositions are mostly Book X, "
            "whose samplers build irrational magnitudes because that is the subject. A "
            "proposition that completes here did so on the rational configurations tried, "
            "which is evidence and not a proof of validity in the rational plane.</p>"
            "<pre>euclid measure --fields</pre>",
        ))

    varies = stats.get("varies", [])
    findings.append((
        "Measured &mdash; four proofs take more than one route through the diagram",
        "<p>A standing worry about old geometry is that a proof may hold only for the "
        "figure its author happened to draw. Each proposition is run on many "
        "configurations and the runs compared, looking for a step that holds in one "
        f"figure and fails in another. <strong>{len(varies)} do</strong>: "
        + ", ".join(
            f'<a href="{_slug(ref)}.html">{ref}</a>' for ref in varies
        )
        + ".</p>"
        "<p>Three of them evaluate a different number of facts depending on where the "
        "points fall &mdash; III.34 checks between four and nine things about the same "
        "theorem &mdash; which means the argument is branching on the picture. III.32 is "
        "the sharper case: a step asserting two points lie on the same side of a line is "
        "true in some configurations and false in others. That is exactly the shape of "
        "the gap Pasch's axiom was later written to close.</p>"
        f"<p>The other {len(all_propositions()) - len(varies)} take the same route "
        "through every figure they are handed. Configurations have to be built to satisfy "
        "a proposition's hypotheses, so one draw in six is now taken from a deliberately "
        "awkward range &mdash; a large denominator puts a point very near a lattice "
        "position without landing on it, which is what makes a triangle nearly flat or a "
        "triple nearly collinear. That range found an assumption Euclid leaves unstated in "
        '<a href="III-14.html">III.14</a>: a chord through the centre is bisected by it, '
        "so the perpendicular he drops has no length and there is no line to draw.</p>"
        '<p><a href="ledger.html">The ledger &rarr;</a></p>'
        "<pre>euclid ledger</pre>",
    ))

    lines = []
    certified = 0
    for euclid_ref, euclid_steps, row in search_rows:
        if not row["found"]:
            continue
        certified += bool(row["exact_minimal"])
        reference = (
            '<a href="{}.html">{}</a>'.format(_slug(euclid_ref), euclid_ref)
            if euclid_ref
            else "&mdash;"
        )
        instrument = "" if row["isa"] == "full" else f" <em>({_esc(row['isa'])})</em>"
        lines.append(
            f"<tr><td>{_esc(row['problem'].replace('-', ' '))}{instrument}</td>"
            f"<td>{reference}</td><td>{euclid_steps or '&mdash;'}</td>"
            f"<td>{row['length']}</td><td>{_strength(row)}</td></tr>"
        )
    if lines:
        findings.append((
            "Exhaustive &mdash; Euclid's first construction cannot be beaten",
            f"<p>For {certified} of these problems every shorter figure was enumerated in "
            "exact arithmetic and none reached the goal, so <em>fewest possible</em> is a "
            "theorem. The two circles of I.1 are the shortest way to an equilateral "
            "triangle, and nothing of one move comes close.</p>"
            "<p>Mohr in 1672 and Mascheroni in 1797 proved the compass alone finds "
            "anything the pair can, and the search puts a price on it: a midpoint costs "
            "<strong>six circles</strong>, and every five-circle figure was enumerated "
            "exactly to prove it cannot be done in five.</p>"
            "<p>That number was seven here until the enumeration reached it. The float "
            "search covered depth six and reported nothing, which is exactly the failure "
            "the exact pass exists to catch: a point pair merged at a tolerance of "
            "10&#8315;&#8311;, or two figures sharing a rounded fingerprint, and a real "
            "construction becomes invisible. The six-circle construction it missed "
            "replays through the kernel and reaches the midpoint.</p>"
            "<p>Some of Euclid's own constructions are far longer than they need to be, "
            "because he builds them out of results already proved, buying certainty "
            "with moves.</p>"
            '<div class="scroll"><table><tr><th>Problem</th><th>Euclid</th><th>His moves'
            f"</th><th>Shortest</th><th>Strength of that claim</th></tr>"
            f"{''.join(lines)}</table></div>"
            "<pre>euclid optimize midpoint --isa compass-only --depth 7</pre>",
        ))

    body = [
        '<p class="kicker">What running the Elements turned up</p>',
        "<h1>Findings</h1>",
        '<p class="lede">Every number on this page was produced by running the corpus, '
        "and each finding carries the command that reproduces it.</p>",
        '<p class="note"><b>Exhaustive</b>: every possibility was enumerated, so a '
        "negative answer is a theorem. <b>Measured</b>: computed exactly from the "
        "constructions as they run. <b>Empirical</b>: sampled over configurations, so it "
        "is evidence, and it says how much. Nothing here is read off the citations "
        'written beside each step. <a href="graph.html">Which edges are which.</a></p>',
        '<p class="note">All of it is measured over <em>this encoding</em> of the '
        "<em>Elements</em>, and the encoding is 390 functions written by hand. Heath's "
        "words are parsed and never retyped; turning them into hypotheses and claims is "
        "authored, and that is the part to doubt. Exact arithmetic catches a claim that "
        "is <em>false</em> the moment it runs. A hypothesis that is merely <em>narrower</em> "
        "than Euclid's makes the proposition weaker and still passes forever, so the "
        "necessity analysis below is also the test for it: a condition doing no work "
        "survives being broken. That is how VIII.8, VIII.10 and VIII.13 were caught "
        "requiring a ratio in least terms, which Euclid nowhere asks for.</p>",
    ]
    for heading, text in findings:
        body.append(f'<div class="finding"><h3>{heading}</h3>{text}</div>')
    body.append(
        '<div class="finding"><h3>Still open</h3>'
        f"<p>All {len(HEATH)} propositions of the thirteen books are here as text; "
        f"{len(all_propositions())} of them have been written out as programs. What is "
        "left is solid geometry: Books XI and XII, and Book XIII from its thirteenth "
        "proposition on. Book XIII's first twelve are plane lemmas about the golden "
        "section and the pentagon, and they are done.</p></div>"
    )
    return _page("Findings — Executable Euclid", "".join(body), here="findings.html")


def _graph_page(graph) -> str:
    rows = "".join(
        f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td><td>{count}</td>'
        f"<td>{graph.depth(ref)}</td><td>{_esc(graph.nodes[ref].statement[:74])}</td></tr>"
        for ref, count in graph.load_bearing()[:16]
    )
    executed, cited = graph.provenance()
    total = executed + cited
    executed_refs = sorted(
        {ref for ref, needed in graph.executed.items() if needed}
        | {required for needed in graph.executed.values() for required in needed},
        key=lambda ref: graph.nodes[ref].sort_key(),
    )
    body = [
        '<p class="kicker">Two kinds of edge, and they are not the same</p>',
        "<h1>What depends on what</h1>",
        '<p class="lede">This graph has two sorts of line in it, and the difference '
        "matters more than the picture does.</p>",
        '<div class="stat">',
        f"<div><b>{executed}</b><span>edges executed</span></div>",
        f"<div><b>{cited}</b><span>edges cited</span></div>",
        f"<div><b>{100 * executed // total if total else 0}%</b><span>executed</span></div>",
        "</div>",
        "<p><strong>Executed.</strong> One proposition calls another as a function, and "
        "the call is recorded as it happens. That edge is a fact about the running code: "
        "delete the earlier proposition and the later one stops working.</p>",
        "<p><strong>Cited.</strong> A reference written beside a step by hand, following "
        "the marginal references in Heath. Those are faithful to the text, and they are "
        "checked &mdash; every citation must name a proposition that exists, and no "
        "proposition may cite a later one &mdash; but they are transcription, not "
        "discovery. A finding read off cited edges is a finding about our typing, so "
        'nothing on the <a href="findings.html">findings page</a> is derived from '
        "them.</p>",
        "<h2>What actually ran</h2>",
        f"<p>The {executed} executed edges on their own, over the "
        f"{len(executed_refs)} propositions that have one. Small enough to read, and "
        "every line in it is a call that happened.</p>",
        f'<div class="plot">{graph_svg(graph, executed_refs, only_executed=True)}</div>',
        "<h2>Everything, both kinds together</h2>",
        f"<p>All {len(graph.nodes)} propositions. This is about ten thousand pixels "
        "wide, so it scrolls at full size: shrunk to a page the labels come out a pixel "
        "tall. Drag it sideways.</p>",
        f'<div class="plot">{graph_svg(graph)}</div>',
        '<p class="legend">'
        "<span><i></i>executed &mdash; a recorded call</span>"
        '<span><i class="dash"></i>cited &mdash; written beside the step</span></p>',
        '<p class="note">Propositions sit on the row matching how many steps of argument '
        "stand between them and the starting rules. Lines run upward from a proposition to "
        "the ones built on it.</p>",
        "<h2>Carrying the most weight</h2>",
        "<p>How many other propositions would fall if this one did &mdash; counting both "
        "kinds of edge, so mostly a summary of Euclid's own cross-references.</p>",
        '<div class="scroll"><table><tr><th>Proposition</th><th>Dependents</th>'
        f"<th>Depth</th><th>Statement</th></tr>{rows}</table></div>",
    ]
    return _page("Dependencies — Executable Euclid", "".join(body),
                 here="graph.html")


def _minimal_page(graph, target: str = "I.47") -> str:
    if target not in graph.nodes:
        return _page("Minimal Elements", "<h1>Nothing to show</h1>")
    minimal = graph.tree_shake(target)
    dropped = sorted(set(graph.nodes) - set(minimal), key=lambda r: graph.nodes[r].sort_key())
    rows = "".join(
        f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td>'
        f"<td>{_esc(graph.nodes[ref].statement)}</td></tr>"
        for ref in minimal
    )
    body = [
        '<p class="kicker">Everything Pythagoras needs, and nothing else</p>',
        f"<h1>The shortest route to {target}</h1>",
        f'<p class="lede">Of the {len(graph.nodes)} propositions written out here, '
        f"{len(minimal)} are needed to reach {target}. Below they are in order, each one "
        "resting only on those above it.</p>",
        '<p class="note">This is computed over both kinds of dependency edge, and most of '
        "them are citations written by hand from Heath's margins. So read this as a "
        "tidy presentation of Euclid's own cross-references. "
        '<a href="graph.html">The split is on the graph page.</a></p>',
        f"<p>{target} is the one shown here because it is the traditional end of Book I "
        "and the obvious thing to aim at. Nothing about the calculation is special to "
        "it &mdash; any proposition can be tree-shaken the same way, and the command "
        "takes whichever you like:</p>",
        "<pre>euclid minimal III.35\neuclid minimal X.115</pre>",
        f'<div class="plot">{graph_svg(graph, minimal, highlight=target)}</div>',
        f'<p class="legend"><span><i></i>executed</span>'
        '<span><i class="dash"></i>cited</span></p>',
        '<div class="scroll"><table><tr><th>Proposition</th><th>Statement</th></tr>'
        f"{rows}</table></div>",
        f"<h2>Left out ({len(dropped)})</h2>",
        '<p class="note">'
        + " ".join(f'<a href="{_slug(ref)}.html">{ref}</a>' for ref in dropped)
        + "</p>",
    ]
    return _page(f"Shortest route to {target}", "".join(body), here="minimal.html")


def _ledger_page(ledgers) -> str:
    totals = (
        sum(item.continuity_debt for item in ledgers),
        sum(len(item.of_kind("order")) for item in ledgers),
        sum(len(item.of_kind("case")) for item in ledgers),
    )
    # Most propositions assume nothing, so listing all 390 produced a table that
    # was four-fifths empty cells and read as broken rather than sparse. Only the
    # rows with something in them are drawn, and the count of the rest is stated.
    owing = [item for item in ledgers if not item.is_clean]
    clean = len(ledgers) - len(owing)
    rows = "".join(
        f'<tr><td><a href="{_slug(item.ref)}.html">{item.ref}</a></td>'
        f"<td class=\"tally\">{item.continuity_debt or '&mdash;'}</td>"
        f"<td class=\"tally\">{len(item.of_kind('order')) or '&mdash;'}</td>"
        f"<td class=\"tally\">{len(item.of_kind('case')) or '&mdash;'}</td>"
        f"<td>{_esc(item.assumptions[0].detail) if item.assumptions else ''}</td></tr>"
        for item in owing
    )
    body = [
        '<p class="kicker">Found by running the proofs, not by reading them</p>',
        "<h1>What Euclid takes on trust</h1>",
        '<p class="lede">His rules let you draw a straight line and a circle. None of them '
        "says two circles ever cross. He uses that anyway, on the first page, and many "
        "times after.</p>",
        '<div class="stat">',
        f"<div><b>{totals[0]}</b><span>points assumed to exist</span></div>",
        f"<div><b>{totals[1]}</b><span>facts read off the picture</span></div>",
        f"<div><b>{totals[2]}</b><span>steps that vary by figure</span></div>",
        "</div>",
        "<h2>What each column counts</h2>",
        "<p><strong>Points assumed to exist.</strong> Every time the construction uses a "
        "point where a line meets a circle, or two circles meet. Euclid's rules never "
        "promise those points are there. This is read straight off the record of what was "
        "drawn, so nothing is missed.</p>",
        "<p><strong>Facts read off the picture.</strong> Claims that one point lies between "
        "two others, or that two points are on the same side of a line &mdash; things the "
        "diagram shows but the argument never establishes.</p>",
        "<p><strong>Steps that vary by figure.</strong> Each proposition is run on many "
        "different figures and the runs compared. A step that holds in one figure but not "
        f"another appears here, and {totals[2]} do &mdash; in "
        + ", ".join(
            f'<a href="{_slug(item.ref)}.html">{item.ref}</a>'
            for item in ledgers if item.of_kind("case")
        )
        + ". Three of them evaluate a different number of facts depending on where the "
        "points fall, which means the proof is taking more than one route through the "
        "diagram; III.32 has a step about two points lying on the same side of a line "
        "that is simply true in some figures and false in others. These are the places "
        "where a case analysis is doing work that the argument does not set out.</p>",
        f"<h2>The {len(owing)} that assume something</h2>",
        f'<p class="note">The other {clean} assume nothing at all &mdash; no '
        "intersection drawn, nothing read off the picture. The last column shows the "
        "first assumption of each; the rest are on the proposition's own page.</p>",
        '<div class="scroll"><table><tr><th>Proposition</th>'
        '<th class="tally">Points assumed</th><th class="tally">Read off</th>'
        '<th class="tally">Varies</th><th>The first of them</th></tr>'
        f"{rows}</table></div>",
    ]
    return _page("What Euclid assumes — Executable Euclid", "".join(body),
                 here="ledger.html")


def _strength(row: dict) -> str:
    """How strong the minimality claim for one row is, in three words or so.

    Three different things, and they were all called "fewest possible":
    every shorter figure ruled out in exact arithmetic; an exhaustive float
    search that found nothing shorter; or a search that ran out of budget.
    """
    if not row.get("found"):
        return "none exists" if row.get("exhaustive") else "none found"
    if row.get("exact_minimal"):
        return "fewest possible"
    if row.get("exhaustive"):
        return "shortest found"
    return "upper bound"


def _optimizer_page(rows) -> str:
    table = []
    for euclid_ref, euclid_steps, row in rows:
        reference = (
            f'<a href="{_slug(euclid_ref)}.html">{euclid_ref}</a>' if euclid_ref else "&mdash;"
        )
        instrument = "" if row["isa"] == "full" else f" <em>({_esc(row['isa'])})</em>"
        table.append(
            f"<tr><td>{_esc(row['problem'].replace('-', ' '))}{instrument}</td>"
            f"<td>{reference}</td>"
            f"<td>{euclid_steps or '&mdash;'}</td>"
            f"<td>{row['length'] if row['found'] else 'none'}</td>"
            f"<td>{_strength(row)}</td>"
            f"<td>{_esc(row['notation'])}</td>"
            f"<td>{'yes' if row['verified'] else '&mdash;'}</td></tr>"
        )
    body = [
        '<p class="kicker">Try everything, then check it exactly</p>',
        "<h1>The shortest constructions</h1>",
        '<p class="lede">The machine tries every legal move, in order of length, until it '
        "reaches the goal. The winner is then rebuilt in exact arithmetic, where it either "
        "works or does not.</p>",
        '<div class="scroll"><table><tr><th>Problem</th><th>Euclid</th><th>His moves</th>'
        "<th>Fewest</th><th>Status</th><th>Cost</th><th>Checked</th></tr>"
        + "".join(table)
        + "</table></div>",
        "<h2>Why Euclid's numbers are bigger</h2>",
        "<p>The two counts measure different things, and the gap is mostly that. "
        "<strong>His moves</strong> counts every line and circle drawn once the earlier "
        "propositions he leans on are expanded &mdash; his I.10 reaches through three other "
        "results, so fifteen things get drawn. <strong>Fewest</strong> stops as soon as the "
        "goal exists and draws nothing to tidy up.</p>"
        "<p>More to the point, Euclid was building constructions that could be "
        "<em>proved</em> from what came before. Reusing an earlier result costs moves but "
        "buys certainty. Counting moves was a nineteenth-century preoccupation, not his.</p>",
        "<h2>Working with fewer tools</h2>",
        "<p>A construction is a program, and these are different machines to run it on: "
        "compass and straightedge, compass alone, straightedge alone with one circle "
        "given, or a compass stuck at one setting. The classical theorems say the compass "
        "alone loses nothing, and the search agrees &mdash; at a price in moves.</p>",
        "<h2>How strong each answer is</h2>",
        "<p>Three different things, and they used all to be called <em>fewest "
        "possible</em>. <strong>Fewest possible</strong> means every shorter figure was "
        "enumerated in the "
        "exact kernel and none reached the goal. No floating point enters that claim, and "
        "neither do the bounds below: the exact enumeration applies no scope limit, no "
        "point limit and no deduplication at all. It is a theorem.</p>"
        "<p><strong>Shortest found.</strong> The search covered every shorter figure it "
        "could represent, but in floating point. A point pair merged at a tolerance of "
        "10&#8315;&#8311;, a tangency lost at 10&#8315;&#8313;, or two different figures "
        "sharing a rounded fingerprint would each hide a construction and turn a longer "
        "answer into a false minimum. Certifying these depths exactly is out of reach.</p>"
        "<p><strong>Upper bound.</strong> The search hit its node budget. Only the "
        "construction shown is meaningful.</p>"
        "<p>The float search is what makes the problem tractable at all, and it carries "
        "two further limits: points straying far outside the figure are ignored, and a "
        "figure of more than twenty points is abandoned. Neither touches a "
        "<em>fewest possible</em> row.</p>",
    ]
    return _page("Shortest constructions — Executable Euclid", "".join(body),
                 here="optimizer.html")


def _text_page() -> str:
    """Where the words come from, and every place they depart from the scan."""
    encoded = {entry.ref for entry in all_propositions()}
    rows = "".join(
        f'<tr><td>{_esc(item["ref"])}</td>'
        f'<td class="mono">{_esc(item["source_reads"])}</td>'
        f'<td class="mono">{_esc(item["corrected_to"])}</td>'
        f'<td>{_esc(item["note"])}</td></tr>'
        for item in ERRATA
    )
    body = [
        '<p class="kicker">Nothing here is paraphrased</p>',
        "<h1>Text and figures</h1>",
        f'<p class="lede">Every proposition statement on this site is '
        f"{HEATH_CREDIT}</p>",
        f"<p>All <strong>{len(HEATH)} propositions</strong> of all thirteen books are "
        "parsed from one source and shipped as data. There is no second kind of "
        "statement: a proposition whose enunciation is missing raises. "
        f"Of the {len(HEATH)}, <strong>{len(encoded)}</strong> have been written out as "
        "programs so far; the rest are text waiting for code.</p>",
        "<h2>Errata</h2>",
        "<p>The source is a scan, and scans misread. Every correction made to it is "
        "listed here in full &mdash; what the scan says, what it was corrected to, and "
        "why. Each is a demonstrable misprint, never a reading of what Euclid meant, "
        "and the parser refuses to run if a correction stops applying.</p>",
        '<div class="scroll"><table><tr><th>Proposition</th><th>The scan reads</th>'
        f"<th>Corrected to</th><th>Why</th></tr>{rows}</table></div>",
        "<h2>The figures are not Euclid's</h2>",
        "<p>The words are his exactly. <strong>The diagrams are not, and are not "
        "meant to be.</strong> If you hold a printed Euclid next to these pages, most "
        "figures will not match.</p>",
        "<p>A figure in a book is <em>composed</em>. The author picks a configuration "
        "that shows the case well, draws the construction lines the argument needs and "
        "no others, and letters the points to suit the proof. Every figure here is a "
        "<em>trace</em>: the record of a construction that actually ran, on coordinates "
        "chosen by a sampler, containing whatever objects the code made, lettered after "
        "the parameters in the code. Three differences follow, and they are permanent:</p>",
        "<ul>"
        "<li>The shapes and the lettering differ, because ours are sampled and his are "
        "chosen.</li>"
        "<li>Ours often carry fewer points. Euclid needs a construction to <em>argue</em> "
        "steps that exact arithmetic settles outright, so his figure holds scaffolding "
        "ours has no use for.</li>"
        "<li>Ours never show an impossible configuration. Where Euclid argues by "
        "contradiction his figure draws the case being refuted &mdash; I.7 shows two "
        "distinct apexes over one base. That configuration does not exist, so it cannot "
        "be constructed here; ours shows the two coincident, which is what the "
        "proposition proves.</li>"
        "</ul>",
        "<p>What the figures do promise: every line and every point in them was really "
        "constructed by the program that verified the proposition, in exact arithmetic. "
        "A proposition's own work is drawn firm; the apparatus it inherited from helper "
        "constructions is drawn back in grey, still present, no longer competing.</p>",
        "<h2>How a misprint gets found</h2>",
        "<p>Two of the three above substitute a single letter and still spell a real "
        "word &mdash; <span class=\"mono\">acutc</span>, <span class=\"mono\">cach</span> "
        "&mdash; so no spell check or length check would catch them. What catches them "
        "is that Euclid's vocabulary is tiny and endlessly repetitive: about four "
        "hundred distinct words across all four hundred and sixty-five enunciations. "
        "The parser lists every word used <em>exactly once</em>, and a misprint has "
        "nowhere to hide in a list that short. Everything else in it is a genuine term "
        "of art.</p>",
    ]
    return _page("Text and figures — Executable Euclid", "".join(body), here="text.html")


def _book_x_page() -> str:
    from ..elements.book10 import classify

    rows = []
    with Context("book-x-site"):
        fourth_root = sqrt(sqrt(2))
        specimens = [
            sqrt(5),
            fourth_root,
            5 + sqrt(24),
            3 + sqrt(2),
            1 + sqrt(5),
            (1 + sqrt(5)) / 2,
            sqrt(2) + sqrt(3),
            3 - sqrt(2),
            sqrt(5) - 1,
            sqrt(3) - sqrt(2),
            fourth_root + sqrt(2) * fourth_root,
            sqrt(2) * fourth_root - fourth_root,
            sqrt(3) * fourth_root + fourth_root,
            sqrt(3) * fourth_root - fourth_root,
            sqrt(18) + sqrt(2),
            sqrt(4 + sqrt(7)),
        ]
        # The last six species are the ones whose two terms are the roots of a
        # single quadratic, so a sum like this is the only way to write them
        # down: give the sum of the squares and the rectangle, and the pair
        # follows. X.39-41 and their duals in X.76-78.
        for squares, rectangle in ((Fraction(1), sqrt(2) / 4),
                                   (sqrt(5), Fraction(1, 2)),
                                   (sqrt(5), sqrt(3) / 2)):
            root = sqrt(squares * squares - 4 * rectangle * rectangle)
            greater, lesser = sqrt((squares + root) / 2), sqrt((squares - root) / 2)
            specimens.append(greater + lesser)
            specimens.append(greater - lesser)
        # And one the thirteen do not reach, so the table shows its own edge
        # rather than only the inside of it. See euclid.measure.gaps.
        specimens.append(1 + sqrt(2) + sqrt(3))
        for value in specimens:
            named = classify(value)
            rows.append(
                f'<tr><td class="mono">{_esc(fmt(value))}</td>'
                f'<td class="mono">{to_float(value):.9f}</td>'
                f"<td>{_esc(named.name)}</td><td>{named.algebraic_degree}</td></tr>"
            )
    body = [
        '<p class="kicker">The book everyone skips</p>',
        "<h1>Book X, running</h1>",
        '<p class="lede">One hundred and fifteen propositions sorting irrational lengths '
        "into named kinds. It reads as impenetrable because it is written about things "
        "nobody could calculate with. This project can.</p>",
        "<p>Some lengths a straightedge and compass produce are whole numbers or "
        "fractions. Most are not. Euclid gives thirteen names to the ones that are not "
        "&mdash; <em>medial</em>, <em>binomial</em>, <em>apotome</em>, and so on &mdash; "
        "each defined by whether certain sums and products come out rational. Every one of "
        "those conditions is a yes-or-no question the exact arithmetic can answer, so the "
        "whole classification becomes a single function.</p>",
        '<div class="scroll"><table><tr><th>Length</th><th>Value</th>'
        f"<th>Euclid's name for it</th><th>Degree</th></tr>{''.join(rows)}</table></div>",
        "<p>All thirteen names are above. The last six are the awkward ones: their two "
        "terms are the roots of a single quadratic, so neither can be written without "
        "the other and the sum shows no seam to split it at. Squaring puts the seam "
        "back &mdash; the square is the sum of the squares plus twice the rectangle, and "
        "<em>those</em> come apart &mdash; after which the recovered pair is checked by "
        "adding it up again.</p>",
        '<p class="note">'
        '<span class="mono">sqrt(18) + sqrt(2)</span> is not a binomial: the two parts are '
        'multiples of each other, so it collapses to <span class="mono">4&middot;sqrt(2)</span>, '
        'and the classifier says so. <span class="mono">sqrt(4 + sqrt 7)</span> untangles '
        "itself before being named. And the second bimedial turns on its rectangle being "
        "a medial <em>area</em> rather than a medial <em>line</em> &mdash; one square "
        "shallower, and a distinction easy to lose.</p>",
        "<h2>Where the thirteen run out</h2>",
        "<p>The last row. "
        '<span class="mono">1 + sqrt(2) + sqrt(3)</span> is constructible with a '
        "straightedge and compass like everything above it, and Euclid has no name for "
        "it. His classification comes out of applying areas, which produces sums and "
        "differences of <em>two</em> terms; this one resolves into three, and falls "
        "outside. It is the simplest such number the search finds. "
        '<a href="findings.html">The finding &rarr;</a></p>',
        "<h2>Try it</h2>",
        '<pre>euclid classify "sqrt(3) + sqrt(5)"\n'
        'euclid classify "(1+sqrt(5))/2"\n'
        "euclid gap</pre>",
    ]
    return _page("Book X — Executable Euclid", "".join(body),
                 here="book-x.html")
