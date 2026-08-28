from __future__ import annotations

import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "sos-contador-api"
SKILL_FILE = SKILL_ROOT / "SKILL.md"


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines and lines[0] == "---", "SKILL.md debe comenzar con frontmatter YAML."
    try:
        closing_index = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError("SKILL.md no cierra su frontmatter YAML.") from exc

    values: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def test_skill_frontmatter_matches_package_name() -> None:
    metadata = parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))

    assert metadata.get("name") == SKILL_ROOT.name
    assert metadata.get("description"), "La descripción de la skill no puede estar vacía."
    assert re.fullmatch(r"[a-z0-9-]{1,64}", metadata["name"])


def test_skill_local_markdown_links_resolve() -> None:
    text = SKILL_FILE.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    local_links = [
        link.split("#", 1)[0]
        for link in links
        if link
        and not link.startswith(("http://", "https://", "mailto:", "#"))
        and not any(marker in link for marker in ("<", ">"))
    ]

    missing = [
        link
        for link in local_links
        if not (SKILL_ROOT / link).resolve().is_file()
    ]
    assert missing == [], f"Referencias locales inexistentes en SKILL.md: {missing}"


def test_public_package_has_no_machine_specific_windows_paths() -> None:
    public_files = [
        path
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".py", ".json", ".yaml", ".yml"}
    ]
    offenders = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path in public_files
        if re.search(r"(?i)[a-z]:\\users\\", path.read_text(encoding="utf-8"))
    ]

    assert offenders == [], f"Rutas específicas de una máquina en el paquete público: {offenders}"
