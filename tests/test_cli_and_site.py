"""The command line and the generated site."""

import re

import pytest

from euclid.cli import main


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


def test_site_builds_without_broken_links(tmp_path):
    assert main(["site", "--out", str(tmp_path), "--no-search"]) == 0
    pages = sorted(tmp_path.glob("*.html"))
    assert len(pages) > 70

    names = {page.name for page in pages}
    broken = set()
    for page in pages:
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.endswith(".html") and href not in names:
                broken.add((page.name, href))
    assert not broken, f"broken links: {sorted(broken)[:5]}"


def test_every_geometric_proposition_gets_a_diagram(tmp_path):
    main(["site", "--out", str(tmp_path), "--no-search"])
    for ref in ("I-1", "I-47", "IV-11", "II-11"):
        page = (tmp_path / f"{ref}.html").read_text(encoding="utf-8")
        assert "<svg" in page, f"{ref} has no figure"
        assert 'class="figure"' in page


def test_the_index_reports_real_numbers(tmp_path):
    main(["site", "--out", str(tmp_path), "--no-search"])
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    stats = dict(
        (label, int(value))
        for value, label in re.findall(r"<b>(\d+)</b><span>([^<]+)</span>", index)
    )
    assert stats["propositions"] > 70
    assert stats["steps checked"] > 500
    assert stats["unproved assumptions"] > 0


def test_statements_are_labelled_with_their_source(tmp_path):
    """A reader must always know whether they are seeing Heath or a summary."""
    main(["site", "--out", str(tmp_path), "--no-search"])
    assert "Heath, 1908" in (tmp_path / "I-47.html").read_text(encoding="utf-8")
    assert "editorial summary" in (tmp_path / "X-36.html").read_text(encoding="utf-8")


def test_the_findings_page_reports_the_real_results(tmp_path):
    main(["site", "--out", str(tmp_path), "--no-search"])
    findings = (tmp_path / "findings.html").read_text(encoding="utf-8")
    for expected in ("I.1", "parallel postulate", "seven circles", "Book X"):
        assert expected in findings


def test_the_site_uses_exactly_three_colours(tmp_path):
    """Black, white, and one grey exactly halfway between. Nothing else."""
    main(["site", "--out", str(tmp_path), "--no-search"])
    found = set()
    for page in tmp_path.glob("*.html"):
        found |= set(re.findall(r"#([0-9a-fA-F]{6})", page.read_text(encoding="utf-8")))
    assert {value.lower() for value in found} == {"000000", "808080", "ffffff"}


def test_the_site_never_fakes_a_fourth_shade(tmp_path):
    """Opacity or alpha would manufacture greys outside the palette."""
    main(["site", "--out", str(tmp_path), "--no-search"])
    style = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "opacity" not in style
    assert "rgba" not in style


def test_theorems_draw_the_figures_they_argue_about(tmp_path):
    """A proposition handed a triangle should still show you the triangle."""
    main(["site", "--out", str(tmp_path), "--no-search"])
    for ref in ("I-41", "I-4", "I-37", "I-20", "VI-4"):
        page = (tmp_path / f"{ref}.html").read_text(encoding="utf-8")
        assert page.count("<line ") >= 3, f"{ref} renders as bare dots"
