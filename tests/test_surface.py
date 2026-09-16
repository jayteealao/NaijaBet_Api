"""Every public method and site key works or raises; the package prints nothing and ships no empty module."""

import ast
import subprocess
import sys
import zipfile
from pathlib import Path

import aiohttp
import pytest

import NaijaBet_Api.id as id_module
from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
from NaijaBet_Api.id import Betid, endpoints

REPO = Path(__file__).resolve().parent.parent
PACKAGE = REPO / "NaijaBet_Api"


@pytest.mark.parametrize("cls", [Bet9ja, Betking, Nairabet, BetkingPlaywright])
def test_stubs_raise_not_implemented(cls):
    instance = cls()
    with pytest.raises(NotImplementedError, match="get_nations"):
        instance.get_nations("x")
    with pytest.raises(NotImplementedError, match="get_competitions"):
        instance.get_competitions()


def test_playwright_async_members_raise_and_open_no_session(monkeypatch):
    constructed = []
    real_init = aiohttp.ClientSession.__init__

    def counting_init(self, *args, **kwargs):
        constructed.append(1)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(aiohttp.ClientSession, "__init__", counting_init)
    playwright_client = BetkingPlaywright()

    with pytest.raises(NotImplementedError, match="get_league"):
        playwright_client.async_get_league(Betid.PREMIERLEAGUE)
    with pytest.raises(NotImplementedError, match="get_all"):
        playwright_client.async_get_all()
    with pytest.raises(NotImplementedError, match="get_league or get_all"):
        playwright_client.async_session  # noqa: B018 - the property raises on access
    assert constructed == []
    assert playwright_client.browser is None


@pytest.mark.parametrize("site", ["bet9ja", "betking", "nairabet"])
def test_to_endpoint_returns_the_league_url(site):
    league = Betid.PREMIERLEAGUE
    expected_id = {"bet9ja": league.bet9ja_id, "betking": league.betking_id, "nairabet": league.nairabet_id}[site]

    assert league.to_endpoint(site) == endpoints[site]["leagues"].format(leagueid=expected_id)


@pytest.mark.parametrize("site", ["sportybet", "nairabetDNB", "", "BET9JA"])
def test_to_endpoint_rejects_unknown_sites(site):
    with pytest.raises(ValueError, match="bet9ja, betking, nairabet"):
        Betid.PREMIERLEAGUE.to_endpoint(site)


def test_sportybet_payload_is_gone():
    assert not hasattr(id_module, "sportybet_payload")


def test_import_installs_no_handler_and_sets_no_level():
    script = (
        "import logging\n"
        "before = len(logging.root.handlers)\n"
        "import NaijaBet_Api.bookmakers\n"
        "import NaijaBet_Api.utils.normalizer\n"
        "print(len(logging.root.handlers) - before, logging.getLogger('NaijaBet_Api').level,"
        " logging.getLogger('NaijaBet_Api.utils.normalizer').level)\n"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True, cwd=REPO)

    assert result.stdout.split() == ["0", "0", "0"]


def print_calls(paths) -> list[str]:
    hits = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                hits.append(f"{path}:{node.lineno}")
    return hits


def test_package_has_no_print_calls(tmp_path):
    assert print_calls(PACKAGE.rglob("*.py")) == []
    rogue = tmp_path / "rogue.py"
    rogue.write_text('def f():\n    print("x")\n', encoding="utf-8")
    assert print_calls([rogue]) == [f"{rogue}:2"]


def test_brotli_body_is_decoded_on_both_paths(stub, league_routes, league_log, brotli_body):
    league_routes(body=brotli_body, headers={"Content-Encoding": "br"}, leagues=[Betid.PREMIERLEAGUE])
    instance = stub()

    sync_rows = instance.get_league(Betid.PREMIERLEAGUE)

    import asyncio

    async def fetch():
        try:
            return await instance.async_get_league(Betid.PREMIERLEAGUE)
        finally:
            await instance.aclose()

    async_rows = asyncio.run(fetch())

    assert len(sync_rows) == 3 and len(async_rows) == 3
    assert sync_rows == async_rows
    assert len(league_log()) == 2


def test_pyproject_requires_brotli():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    dependencies = text.split("dependencies = [", 1)[1].split("]", 1)[0]

    assert "brotli" in dependencies.lower()


@pytest.mark.timeout(180)
def test_wheel_has_no_empty_modules_and_module_run_fails(tmp_path):
    # Without --wheel the wheel is built from the fresh sdist, so a stale build/lib in the checkout cannot leak in.
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(tmp_path)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    names = zipfile.ZipFile(wheel).namelist()

    assert "NaijaBet_Api/__main__.py" not in names
    assert not [name for name in names if name.startswith("NaijaBet_Api/schema/")]
    assert "NaijaBet_Api/utils/logger.py" not in names

    run = subprocess.run([sys.executable, "-m", "NaijaBet_Api"], capture_output=True, text=True, cwd=tmp_path)

    assert run.returncode != 0
    assert "No module named" in run.stderr
