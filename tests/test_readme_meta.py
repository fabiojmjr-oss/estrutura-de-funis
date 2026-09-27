"""The claims a README makes about the repository itself, which the figure tests do not cover.

`tests/test_readme_claims.py` asserts every number derived from the synthetic data. It cannot see a
different class of statement: claims about the repository. Test counts, the module table, links to
the examples and templates, and whether a draft placeholder was ever filled in are assertions
about this repository rather than about a funnel. The sister repository shipped two defects of
exactly this class before it had these tests, so this one starts with them.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = ("TIMING_", "PLACEHOLDER", "TODO", "FIXME", "XXX", "lorem ipsum", "TBD")
READMES = ("README.md", "README.pt-BR.md")


def markdown_files() -> list[Path]:
    """Every documentation file, excluding anything git would not track."""
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and "node_modules" not in path.parts
    )


def collected(marker: str) -> int:
    """Count the tests pytest collects under a marker expression, without running them."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
        + ["-m", marker],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    counts = re.findall(r"^\S+\.py:\s*(\d+)$", result.stdout, re.M)
    if not counts:
        pytest.fail(f"could not read collected counts from pytest output:\n{result.stdout[-2000:]}")
    return sum(int(count) for count in counts)


def test_no_placeholder_survives_into_the_documentation() -> None:
    offenders = []
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for token in PLACEHOLDERS:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert not offenders, "placeholder tokens left in documentation: " + "; ".join(offenders)


def test_the_readmes_quote_the_number_of_tests_that_exist() -> None:
    """Both language editions, because a count corrected in one and not the other is the same bug."""
    fast = collected("not slow")
    total = fast + collected("slow")
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    portuguese = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")
    patterns = (
        (english, r"\*\*(\d[\d,]*) tests,", total),
        (english, r"(\d[\d,]*) of them run in", fast),
        (portuguese, r"\*\*(\d[\d.]*) testes,", total),
        (portuguese, r"(\d[\d.]*) deles rodam em", fast),
    )
    for text, pattern, expected in patterns:
        match = re.search(pattern, text)
        assert match is not None, f"could not find {pattern!r} in a README"
        assert int(re.sub(r"[,.]", "", match.group(1))) == expected, pattern


def test_the_module_table_lists_every_module_and_no_others() -> None:
    packages = {path.parent.name for path in (ROOT / "src" / "funilab").glob("*/__init__.py")}
    for readme in READMES:
        text = (ROOT / readme).read_text(encoding="utf-8")
        listed = set(re.findall(r"^\| `funilab\.(\w+)` \|", text, re.M))
        assert listed == packages, f"{readme}: table {sorted(listed)} vs package {sorted(packages)}"


def test_every_module_readme_is_bilingual() -> None:
    for path in sorted((ROOT / "src" / "funilab").glob("*/README.md")):
        text = path.read_text(encoding="utf-8")
        assert "## Português" in text, f"{path.relative_to(ROOT)} has no Portuguese section"


def test_both_root_readmes_document_the_same_findings() -> None:
    numbers = [
        re.findall(r"^### (\d+)\.", (ROOT / readme).read_text(encoding="utf-8"), re.M)
        for readme in READMES
    ]
    assert numbers[0] == numbers[1]
    assert [int(n) for n in numbers[0]] == list(range(1, len(numbers[0]) + 1))


def test_every_example_is_referenced_by_both_readmes() -> None:
    scripts = sorted(path.name for path in (ROOT / "examples").glob("*.py"))
    assert scripts
    for readme in READMES:
        text = (ROOT / readme).read_text(encoding="utf-8")
        missing = [name for name in scripts if f"examples/{name}" not in text]
        assert not missing, f"{readme} does not link {missing}"


def test_every_template_is_referenced_by_the_playbook() -> None:
    playbook = (ROOT / "docs" / "ciclo-ideia-mvp.md").read_text(encoding="utf-8")
    templates = sorted(path.name for path in (ROOT / "templates").glob("*.md"))
    assert templates
    missing = [name for name in templates if f"templates/{name}" not in playbook]
    assert not missing, f"templates not linked from the playbook: {missing}"


def test_relative_links_resolve() -> None:
    """A link to a file that does not exist is a claim about the repository that is false."""
    broken = []
    for path in markdown_files():
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (path.parent / target).resolve().exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not broken, "broken relative links: " + "; ".join(broken)


def test_the_readmes_quote_the_number_of_javascript_tests() -> None:
    """The web suites are not collected by pytest, so their counts are checked from the source."""

    def count(directory: str, suffix: str) -> int:
        files = (ROOT / "web" / directory).glob(f"*{suffix}")
        return sum(len(re.findall(r"^test\(", f.read_text(encoding="utf-8"), re.M)) for f in files)

    unit = count("tests", ".test.mjs")
    browser = count("e2e", ".e2e.mjs")
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    portuguese = (ROOT / "README.pt-BR.md").read_text(encoding="utf-8")
    assert f"**{unit} JavaScript tests**" in english
    assert f"**{browser} browser tests**" in english
    assert (
        f"**{unit} testes\nJavaScript**" in portuguese
        or f"**{unit} testes JavaScript**" in portuguese
    )
    assert f"**{browser} testes de navegador**" in portuguese
