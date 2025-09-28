import os
from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest

from ebf_core.fileutil.executable_finder import ExecutableFinder


# region fixtures
@pytest.fixture
def system_path_with_fake_exes(tmp_path: Path, monkeypatch) -> Callable[..., list[str]]:
    """
    Create fake executables in a temp bin dir and patch PATH (and PATHEXT on Windows).
    Returns the list of names you asked it to create, e.g. ["foo", "bar"].
    """

    def _factory(*names: str) -> list[str]:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)

        for n in names:
            exe = bin_dir / (f"{n}.exe" if os.name == "nt" else n)
            exe.write_text("")
            if os.name != "nt":  # make it executable on POSIX
                exe.chmod(0o755)

        monkeypatch.setenv("PATH", str(bin_dir))
        if os.name == "nt":
            monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")

        return list(names)

    return _factory


@pytest.fixture
def sut() -> ExecutableFinder:
    return ExecutableFinder()


# endregion


class TestFindOnSystemPath:
    def test_can_find_executable_on_path(self, sut: ExecutableFinder, system_path_with_fake_exes):
        exe_names = system_path_with_fake_exes("foo")

        found = sut.find_on_system_path(exe_names)
        assert found.stem == "foo"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only")
    def test_can_find_executable_if_extension_is_included_and_os_is_windows(
            self, sut: ExecutableFinder, system_path_with_fake_exes):
        system_path_with_fake_exes("foo")
        found = sut.find_on_system_path(["foo.exe"])
        assert found is not None and found.name == "foo.exe"

    def test_missing_executable_names_are_ignored(self, sut: ExecutableFinder, system_path_with_fake_exes):
        system_path_with_fake_exes("foo")
        search_names = list(["bar", "foo"])  # 'bar' isn't there

        found = sut.find_on_system_path(search_names)
        assert found.stem == "foo"

    def test_returns_none_when_no_executable_names_are_present(self, sut: ExecutableFinder):
        assert sut.find_on_system_path(["does-not-exist"]) is None

    @pytest.mark.parametrize("targets", [[], None])
    def test_returns_none_when_list_is_empty_or_none(self, sut: ExecutableFinder, targets):
        assert sut.find_on_system_path(targets) is None


class TestFindStartMenuShortcut:
    @staticmethod
    def _mk_start_menu_tree(root: Path) -> Path:
        tree = root / r"Microsoft\Windows\Start Menu\Programs"
        (tree / "Fidelity Investments").mkdir(parents=True, exist_ok=True)
        return tree

    def test_prefers_user_shortcut_over_machine(self, sut: ExecutableFinder, tmp_path: Path):
        progdata = tmp_path / "progdata"
        appdata = tmp_path / "appdata"
        machine = self._mk_start_menu_tree(progdata) / "Fidelity Investments" / "Active Trader Pro.lnk"
        user = self._mk_start_menu_tree(appdata) / "Fidelity Investments" / "Active Trader Pro.lnk"
        machine.write_text("")
        user.write_text("")

        with patch.dict(
                os.environ,
                {"PROGRAMDATA": str(progdata), "APPDATA": str(appdata)},
                clear=False,
        ):
            p = sut.find_start_menu_shortcut(
                vendor_folders=["Fidelity Investments"],
                patterns=["*active*trader*pro*.lnk", "*fidelity*.lnk"],
            )
        assert p == user.resolve()

    def test_pattern_specificity_wins(self, sut: ExecutableFinder, tmp_path: Path):
        appdata = tmp_path / "appdata"
        base = self._mk_start_menu_tree(appdata) / "Fidelity Investments"
        general = base / "Fidelity.lnk"
        specific = base / "Active Trader Pro.lnk"
        general.write_text("")
        specific.write_text("")

        with patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False):
            p = sut.find_start_menu_shortcut(
                vendor_folders=["Fidelity Investments"],
                patterns=["*active*trader*pro*.lnk", "*fidelity*.lnk"],
            )
        assert p == specific.resolve()

    def test_none_when_no_candidates(self, sut: ExecutableFinder, tmp_path: Path):
        with patch.dict(
                os.environ,
                {
                    "PROGRAMDATA": str(tmp_path / "pd"),
                    "APPDATA": str(tmp_path / "ad"),
                },
                clear=False,
        ):
            assert (
                    sut.find_start_menu_shortcut(
                        vendor_folders=["Fidelity Investments"], patterns=["*.lnk"]
                    )
                    is None
            )



class TestFindInCommonRoots:
    def test_glob_search_finds_first_match(self, sut: ExecutableFinder, tmp_path: Path):
        pf = tmp_path / "ProgramFiles"
        pfx86 = tmp_path / "ProgramFiles(x86)"
        local = tmp_path / "LocalAppData"
        pdata = tmp_path / "ProgramData"
        for d in (pf, pfx86, local, pdata):
            d.mkdir(parents=True, exist_ok=True)
        target = pf / "Fidelity" / "Active Trader Pro" / "bin" / ("atp.exe" if os.name == "nt" else "atp")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("")

        with patch.dict(
                os.environ,
                {
                    "ProgramFiles": str(pf),
                    "ProgramFiles(x86)": str(pfx86),
                    "LOCALAPPDATA": str(local),
                    "ProgramData": str(pdata),
                },
                clear=False,
        ):
            p = sut.find_in_common_roots(["**/Fidelity*/Active*Trader*Pro*/**/*"])
        assert p == target.resolve()

    def test_returns_none_when_no_match(self, sut: ExecutableFinder, tmp_path: Path):
        with patch.dict(
                os.environ,
                {
                    "ProgramFiles": str(tmp_path / "pf"),
                    "ProgramFiles(x86)": str(tmp_path / "pfx86"),
                    "LOCALAPPDATA": str(tmp_path / "lad"),
                    "ProgramData": str(tmp_path / "pd"),
                },
                clear=False,
        ):
            assert sut.find_in_common_roots(["**/*.exe"]) is None


class TestBestOf:
    def test_best_of_returns_first_existing(self, sut: ExecutableFinder, tmp_path: Path):
        a = tmp_path / "a.exe"
        b = tmp_path / "b.exe"
        b.write_text("")
        c = tmp_path / "c.exe"
        got = sut.best_of(a, None, b, c)
        assert got == b.resolve()
