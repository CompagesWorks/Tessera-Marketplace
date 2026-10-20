import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
INDEX = ROOT / "marketplace.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "CompagesWorks/Tessera-Marketplace")
BRANCH = os.environ.get("MARKETPLACE_BRANCH", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/plugins/"
PLUGIN_ID = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
ICON_NAME = re.compile(r"^[a-z0-9-]{1,40}$")


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
    }


def main():
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {"name": "Tessera Marketplace", "plugins": []}
    previous = {p["id"]: p for p in index.get("plugins", [])}
    newest = {}
    for file in sorted(PLUGINS.glob("*.tessera-plugin")):
        entry = read_package(file)
        current = newest.get(entry["id"])
        if current is None or version_key(entry["version"]) > version_key(current["version"]):
            newest[entry["id"]] = entry

    plugins = []
    for entry in newest.values():
        merged = {**previous.get(entry["id"], {}), **entry}
        if merged.get("icon") is None:
            merged.pop("icon", None)
        plugins.append(merged)
    for old in previous.values():
        if old["id"] not in newest and not old.get("download", "").startswith(RAW):
            plugins.append(old)
    plugins.sort(key=lambda p: p["id"])

    index["plugins"] = plugins
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(plugins)} plugin(s) listed")


if __name__ == "__main__":
    main()
