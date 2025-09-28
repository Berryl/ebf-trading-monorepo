import os
from pathlib import Path
from unittest.mock import patch
import pytest

# noinspection SpellCheckingInspection
PGM_FILES_STR = "PROGRAMFILES"

from ebf_core.fileutil.executable_finder import (
    find_on_system_path,
    find_start_menu_shortcut,
    find_in_common_roots,
    best_of,
)


@pytest.fixture(params=[[], None])
def targets(request):
    return request.param


@pytest.fixture
def system_path_with_fake_exes(tmp_path, monkeypatch):

    def _make_exes(*names: str) -> list[str]:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        made = []
        for n in names:
            p = bin_dir / n
            p.write_text("echo")
            p.chmod(0o755)
            made.append(str(p))
            # Windows: if the caller passes "foo" (no ext), the resolver will look for foo.exe/.bat/.cmd.
            # Create foo.exe so the search via PATHEXT succeeds.
            if os.name == "nt":
                root, ext = os.path.splitext(n)
                if not ext:  # only when the requested name had no extension
                    (bin_dir / f"{n}.exe").write_text("echo")
        # Ensure our bin is searched and PATHEXT expansion works
        monkeypatch.setenv("PATH", str(bin_dir))
        if os.name == "nt":
            monkeypatch.setenv("PATHEXT", ".EXE;.BAT;.CMD")
        return list(names)
    return _make_exes


class TestFindOnSystemPath:
    def test_can_find_executable_on_path(self, system_path_with_fake_exes):
        exe_names = system_path_with_fake_exes("foo")
        found = find_on_system_path(exe_names)
        assert found.stem == "foo"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only PATHEXT semantics")
    def test_can_find_executable_on_path_with_windows_extension(self, system_path_with_fake_exes):
        exe_names = system_path_with_fake_exes("foo.bat")
        found = find_on_system_path(exe_names)
        assert found.stem == "foo"

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only PATHEXT semantics")
    def test_can_find_windows_name_without_extension(self, tmp_path, monkeypatch):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "foo").write_text("echo")  # no extension
        monkeypatch.setenv("PATH", str(bin_dir))
        monkeypatch.setenv("PATHEXT", ".EXE;.BAT;.CMD")
        assert find_on_system_path(["foo"]) is None

    def test_can_find_when_name_is_absolute_path(self, tmp_path):
        exe = tmp_path / "foo"
        exe.write_text("echo")
        exe.chmod(0o755)
        found = find_on_system_path([str(exe)])
        assert found.resolve() == exe.resolve()

    def test_executable_names_not_in_system_path_are_ignored(self, system_path_with_fake_exes):
        system_path_with_fake_exes("foo")  # only create foo (and foo.exe on Windows)
        search_names = ["missing", "foo"]  # "missing" does not exist

        found = find_on_system_path(search_names)
        assert found.stem == "foo", "the missing name should not affect finding foo"

    def test_names_order_wins(self, system_path_with_fake_exes):
        system_path_with_fake_exes("bar", "foo")
        found = find_on_system_path(["foo", "bar"])
        assert found.stem == "foo"

    def test_returns_none_when_no_executable_name_is_not_in_system(self):
        assert find_on_system_path(["does-not-exist"]) is None

    @pytest.mark.parametrize("targets", [[], None])
    def test_returns_none_when_list_is_empty_or_none(self, targets):
        assert find_on_system_path(targets) is None

    def test_returns_none_when_path_is_empty(self, monkeypatch):
        monkeypatch.delenv("PATH", raising=False)
        assert find_on_system_path(["foo"]) is None


class TestFindStartMenuShortcut:
    def test_prefers_user_shortcut_over_machine(self, tmp_path: Path):
        appdata = tmp_path / "appdata"
        machine = tmp_path / "machine"
        user_shortcut = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Fidelity Investments" / "Fidelity.lnk"
        machine_shortcut = machine / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Fidelity Investments" / "Active Trader Pro.lnk"
        user_shortcut.parent.mkdir(parents=True)
        machine_shortcut.parent.mkdir(parents=True)
        user_shortcut.write_text("")
        machine_shortcut.write_text("")

        with patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False):
            p = find_start_menu_shortcut(
                vendor_folders=["Fidelity Investments"],
                patterns=["*fidelity*.lnk", "*active*trader*pro*.lnk"],
            )
        assert p == user_shortcut

    def test_pattern_specificity_wins(self, tmp_path: Path):
        appdata = tmp_path / "appdata"
        shortcut1 = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Fidelity Investments" / "Fidelity.lnk"
        shortcut2 = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Fidelity Investments" / "Active Trader Pro.lnk"
        shortcut1.parent.mkdir(parents=True)
        shortcut1.write_text("")
        shortcut2.write_text("")

        with patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False):
            p = find_start_menu_shortcut(
                vendor_folders=["Fidelity Investments"],
                patterns=["*active*trader*pro*.lnk", "*fidelity*.lnk"],
            )
        assert p == shortcut2

    def test_none_when_no_candidates(self, tmp_path: Path):
        with patch.dict(
            os.environ,
            {
                "APPDATA": str(tmp_path / "appdata"),
                "PROGRAMDATA": str(tmp_path / "programdata"),
            },
            clear=False,
        ):
            assert (
                find_start_menu_shortcut(
                    vendor_folders=["Fidelity Investments"],
                    patterns=["*active*trader*pro*.lnk", "*fidelity*.lnk"],
                )
                is None
            )


class TestFindInCommonRoots:

    def test_glob_search_finds_first_match(self, tmp_path: Path):
        program_files = tmp_path / "Program Files"
        program_files_x86 = tmp_path / "Program Files (x86)"
        exe_path = program_files / "Fidelity Investments" / "Active Trader Pro" / "ATP.exe"
        exe_path.parent.mkdir(parents=True)
        exe_path.write_text("")

        with patch.dict(
            os.environ,
            {
                PGM_FILES_STR: str(program_files),
                f"{PGM_FILES_STR}(X86)": str(program_files_x86),
            },
            clear=False,
        ):
            p = find_in_common_roots(["**/Fidelity*/Active*Trader*Pro*/**/*"])
        assert p == exe_path.resolve()

    def test_returns_none_when_no_match(self, tmp_path: Path):
        with patch.dict(
                os.environ,
                {
                    PGM_FILES_STR: str(tmp_path / "Program Files"),
                    f"{PGM_FILES_STR}(X86)": str(tmp_path / "Program Files (x86)"),
                    "LOCALAPPDATA": str(tmp_path / "LocalAppData"),
                    "ProgramData": str(tmp_path / "ProgramData"),
                },
                clear=False,
        ):
            assert find_in_common_roots(["**/*.exe"]) is None


class TestBestOf:
    def test_best_of_returns_first_existing(self, tmp_path: Path):
        a = tmp_path / "a.exe"
        b = tmp_path / "b.exe"
        b.write_text("")
        c = tmp_path / "c.exe"
        got = best_of(a, None, b, c)
        assert got == b.resolve()
