import hashlib
import html
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
ICONS = ROOT / "assets" / "icons"
INDEX = ROOT / "marketplace.json"
README = ROOT / "README.md"
REPO = os.environ.get("GITHUB_REPOSITORY", "CompagesWorks/Tessera-Marketplace")
BRANCH = os.environ.get("MARKETPLACE_BRANCH", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/plugins/"
ICON_CDN = "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.13.2/icons/{}.svg"
ICON_COLOR = "#9b8cff"
PLUGIN_ID = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
ICON_NAME = re.compile(r"^[a-z0-9-]{1,40}$")
START, END = "<!-- plugins:start -->", "<!-- plugins:end -->"


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def version_key(version):
    return [int(part) if part.isdigit() else 0 for part in re.split(r"[.-]", version.lstrip("vV"))[:3]]


def localize(value, locale):
    match = re.fullmatch(r"%([\w.-]+)%", value or "")
    return locale.get(match.group(1), value) if match else value


def read_package(file):
    with zipfile.ZipFile(file) as archive:
        names = set(archive.namelist())
        if "tessera-package.json" not in names or "manifest.json" not in names:
            fail(f"{file.name}: not a package built with tessera-plugin pack")
        manifest = json.loads(archive.read("manifest.json"))
        locale = json.loads(archive.read("locales/en.json")) if "locales/en.json" in names else {}
        icon = manifest.get("icon") or "puzzle"
        image = archive.read(icon) if icon in names and not ICON_NAME.match(icon) else None
    for key in ("id", "name", "version"):
        if not manifest.get(key):
            fail(f"{file.name}: manifest.json has no {key}")
    if not PLUGIN_ID.match(manifest["id"]):
        fail(f"{file.name}: invalid id {manifest['id']}")
    return {
        "id": manifest["id"],
        "name": localize(manifest["name"], locale),
        "author": localize(manifest.get("author", ""), locale),
        "version": manifest["version"],
        "description": localize(manifest.get("description", ""), locale),
        "icon": icon if ICON_NAME.match(icon) else None,
        "download": RAW + file.name,
        "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
    }, image, Path(icon).suffix


def icon_file(entry, image, suffix):
    ICONS.mkdir(parents=True, exist_ok=True)
    if image is not None:
        target = ICONS / f"{entry['id']}{suffix}"
        target.write_bytes(image)
        return target
    name = entry["icon"] or "puzzle"
    target = ICONS / f"{name}.svg"
    if not target.exists():
        try:
            svg = urllib.request.urlopen(ICON_CDN.format(name), timeout=20).read().decode()
        except Exception:
            print(f"warning: no Bootstrap icon named {name}", file=sys.stderr)
            return icon_file({**entry, "icon": "puzzle"}, None, "") if name != "puzzle" else None
        svg = svg.replace('fill="currentColor"', f'fill="{ICON_COLOR}"').replace('width="16" height="16"', 'width="64" height="64"')
        target.write_text(svg, encoding="utf-8")
    return target


def cell(text):
    return html.escape(str(text or ""), quote=False).replace("|", "&#124;").replace("\n", " ")


def catalog(entries, icons):
    if not entries:
        return "_No plugins yet._"
    rows = ["| Plugin | What it does | Version |", "|---|---|:-:|"]
    for entry in sorted(entries, key=lambda e: e["name"].lower()):
        icon = icons.get(entry["id"])
        image = f'<img src="{icon.relative_to(ROOT).as_posix()}" width="40" height="40" alt=""><br>' if icon else ""
        author = f"<br><sub>by {cell(entry.get('author'))}</sub>" if entry.get("author") else ""
        rows.append(f"| {image}**{cell(entry['name'])}**{author} | {cell(entry.get('description'))} | `{cell(entry['version'])}` |")
    return "\n".join(rows)


def main():
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {"name": "Tessera Marketplace", "plugins": []}
    previous = {p["id"]: p for p in index.get("plugins", [])}
    newest = {}
    for file in sorted(PLUGINS.glob("*.tessera-plugin")):
        entry, image, suffix = read_package(file)
        current = newest.get(entry["id"])
        if current is None or version_key(entry["version"]) > version_key(current[0]["version"]):
            newest[entry["id"]] = (entry, image, suffix)

    plugins, icons = [], {}
    for entry, image, suffix in newest.values():
        merged = {**previous.get(entry["id"], {}), **entry}
        if merged.get("icon") is None:
            merged.pop("icon", None)
        plugins.append(merged)
        icons[entry["id"]] = icon_file(entry, image, suffix)
    for old in previous.values():
        if old["id"] not in newest and not old.get("download", "").startswith(RAW):
            plugins.append(old)
            icons[old["id"]] = icon_file(old if ICON_NAME.match(old.get("icon") or "") else {**old, "icon": None}, None, "")
    plugins.sort(key=lambda p: p["id"])

    index["plugins"] = plugins
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        fail(f"README.md needs {START} and {END} markers")
    before, rest = readme.split(START, 1)
    after = rest.split(END, 1)[1]
    README.write_text(f"{before}{START}\n{catalog(plugins, icons)}\n{END}{after}", encoding="utf-8")
    print(f"{len(plugins)} plugin(s) listed")


if __name__ == "__main__":
    main()
