"""Every host the package names traces to a recorded browser session."""

import json
import re
import subprocess
from pathlib import Path

import pytest

from NaijaBet_Api.id import Betid

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "NaijaBet_Api"
MANIFEST = REPO / "tests" / "fixtures" / "endpoint-provenance.json"
HOST_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")


def hosts_in(paths) -> dict[str, set[str]]:
    """Map every host literal to the files that name it."""
    found: dict[str, set[str]] = {}
    for path in paths:
        for host in HOST_RE.findall(path.read_text(encoding="utf-8")):
            found.setdefault(host, set()).add(str(path))
    return found


def assert_hosts_recorded(paths, manifest: dict) -> None:
    recorded = {entry["host"] for entry in manifest["hosts"]}
    unknown = {host: files for host, files in hosts_in(paths).items() if host not in recorded}
    assert not unknown, f"hosts without a provenance entry: {unknown}"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_every_package_host_has_a_recorded_entry(manifest):
    assert manifest["recorded-at"]
    assert manifest["egress"]["city"] and manifest["egress"]["provider"]
    assert_hosts_recorded(PACKAGE.rglob("*.py"), manifest)


def test_an_unrecorded_host_fails_and_is_named(tmp_path, manifest):
    module = tmp_path / "rogue.py"
    module.write_text('URL = "https://example.invalid/feed"\n', encoding="utf-8")

    with pytest.raises(AssertionError, match="example.invalid"):
        assert_hosts_recorded([*PACKAGE.rglob("*.py"), module], manifest)


def test_nairabet_api_host_moved_off_the_dead_host(manifest):
    api_hosts = {
        entry["host"] for entry in manifest["hosts"] if entry["bookmaker"] == "nairabet" and entry["role"] == "api"
    }

    assert api_hosts and "sports-api.nairabet.com" not in api_hosts
    assert manifest["resolver"]
    assert any(entry["host"] == "sports-api.nairabet.com" for entry in manifest["superseded"])


@pytest.mark.parametrize("bookmaker", ["bet9ja", "betking", "nairabet"])
def test_library_url_equals_the_recorded_sample(manifest, bookmaker):
    entry = next(entry for entry in manifest["hosts"] if entry["bookmaker"] == bookmaker and entry["role"] == "api")

    assert entry["status"] == 200
    assert Betid.PREMIERLEAGUE.to_endpoint(bookmaker) == entry["sample-url"]


def test_no_har_is_tracked_and_gitignore_names_it():
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout

    assert not [line for line in tracked.splitlines() if line.endswith(".har")]
    assert "*.har" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
