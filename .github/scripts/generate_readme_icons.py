from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "profile-icons.txt"
README_PATH = REPO_ROOT / "README.md"

CONNECT_START = "<!-- icons:connect:start -->"
CONNECT_END = "<!-- icons:connect:end -->"
TOOLS_START = "<!-- icons:tools:start -->"
TOOLS_END = "<!-- icons:tools:end -->"

DEVICON_BASE = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons"
SOCIAL_ICON_ALIASES = {
    "x": "twitter",
}


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def parse_config(config_text: str) -> tuple[list[tuple[str, str | None]], list[tuple[str, str | None]]]:
    section = ""
    connect: list[tuple[str, str | None]] = []
    tools: list[tuple[str, str | None]] = []

    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue

        if section not in {"connectwithme", "languagesandtools"}:
            continue

        if "=" in line:
            raw_name, raw_url = line.split("=", 1)
            raw_name = raw_name.strip()
            raw_url = raw_url.strip()

            if is_url(raw_name):
                name = raw_name
            else:
                name = raw_name.lower()

            url = raw_url or None
        else:
            raw_name = line.strip()
            if is_url(raw_name):
                name = raw_name
            else:
                name = raw_name.lower()
            url = None

        if not name:
            continue

        if section == "connectwithme":
            connect.append((name, url))
        else:
            tools.append((name, url))

    return connect, tools


def icon_url(name: str) -> str:
    if is_url(name):
        return name

    icon_name = SOCIAL_ICON_ALIASES.get(name, name)
    return f"{DEVICON_BASE}/{icon_name}/{icon_name}-original.svg"


def build_connect_html(items: list[tuple[str, str | None]]) -> list[str]:
    lines = ["<p align=\"left\">"]
    for name, link in items:
        image = f"<img src=\"{icon_url(name)}\" width=\"40\" height=\"40\" alt=\"{name}\" />"
        if link:
            lines.append(f"<a href=\"{link}\" target=\"_blank\" rel=\"noreferrer\">{image}</a>")
        else:
            lines.append(image)
    lines.append("</p>")
    return lines


def build_tools_html(items: list[tuple[str, str | None]]) -> list[str]:
    lines = ["<p align=\"left\">"]
    for name, link in items:
        image = f"<img src=\"{icon_url(name)}\" width=\"40\" height=\"40\" alt=\"{name}\" />"
        if link:
            lines.append(f"<a href=\"{link}\" target=\"_blank\" rel=\"noreferrer\">{image}</a>")
        else:
            lines.append(image)
    lines.append("</p>")
    return lines


def replace_marked_block(readme_text: str, start_marker: str, end_marker: str, block_lines: list[str]) -> str:
    start_index = readme_text.find(start_marker)
    end_index = readme_text.find(end_marker)

    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError(f"Brakuje markerów w README: {start_marker} ... {end_marker}")

    before = readme_text[: start_index + len(start_marker)]
    after = readme_text[end_index:]
    block = "\n" + "\n".join(block_lines) + "\n"
    return before + block + after


def main() -> None:
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    readme_text = README_PATH.read_text(encoding="utf-8")

    connect_items, tool_items = parse_config(config_text)
    connect_html = build_connect_html(connect_items)
    tools_html = build_tools_html(tool_items)

    updated = replace_marked_block(readme_text, CONNECT_START, CONNECT_END, connect_html)
    updated = replace_marked_block(updated, TOOLS_START, TOOLS_END, tools_html)

    if updated != readme_text:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
