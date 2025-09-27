import os
from pathlib import Path


class ExecutableFinder:

    @staticmethod
    def find_on_system_path(names: list[str] | None) -> Path | None:
        """
        Return the first executable found by scanning the SYSTEM PATH.

        Deterministic search: iterate `names` in order; for each, scan PATH entries in order.
        If a name is absolute, validate it directly and return if executable.

        Windows:
          - If name includes an extension (e.g., "foo.exe"), check it as-is.
          - If no extension, expand PATHEXT (env or default ".COM;.EXE;.BAT;.CMD") in order.
          - Also check os.access(..., X_OK) for symmetry with POSIX.

        POSIX:
          - Require the file to exist and be executable (os.access(..., X_OK)).

        Args:
            names: Candidate executable base names (e.g., ["foo", "bar"]). If None or empty, returns None.

        Returns:
            Path | None: Resolved path to the first match, or None if nothing is found.
        """
        if not names:
            return None

        path_dirs = [Path(p) for p in os.environ.get("PATH", "").split(os.pathsep) if p]
        if not path_dirs:
            path_dirs = []

        def _win_extensions() -> list[str]:
            exe_extensions = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
            out: list[str] = []
            for e in exe_extensions:
                e = e.strip()
                if not e:
                    continue
                out.append(e if e.startswith(".") else f".{e}")
            return out

        for raw in names:
            if not raw:
                continue
            name = raw.strip().strip('"').strip("'")

            # Absolute path: validate directly, skip PATH scan
            p = Path(name)
            if p.is_absolute():
                if p.exists() and (os.name == "nt" or os.access(p, os.X_OK)):
                    return p.resolve()
                continue

            if os.name != "nt":
                for d in path_dirs:
                    cand = d / name
                    if cand.exists() and os.access(cand, os.X_OK):
                        return cand.resolve()
                continue

            base, ext = os.path.splitext(name)
            if ext:
                for d in path_dirs:
                    cand = d / name
                    if cand.exists() and os.access(cand, os.X_OK):
                        return cand.resolve()
            else:
                for d in path_dirs:
                    for e in _win_extensions():
                        cand = d / f"{name}{e}"
                        if cand.exists() and os.access(cand, os.X_OK):
                            return cand.resolve()

        return None

    def find_start_menu_shortcut(self, vendor_folders: list[str], patterns: list[str]) -> Path | None:
        """
        Searches for a Start Menu shortcut by scanning provided vendor folders and matching
        against specified patterns.

        This method iterates through the given vendor folders and attempts to locate a shortcut
        that matches any of the provided string patterns. If a match is found, it returns the
        path to the corresponding shortcut file; otherwise, it returns None.

        Parameters:
        vendor_folders: list[str]
            A list of vendor folders to search for the Start Menu shortcut.
        patterns: list[str]
            Patterns used to match the shortcut files in the vendor folders.

        Returns:
        Path | None
            The path to the matched shortcut file if found; otherwise, None.
        """
        pass

    def find_in_common_roots(self, globs: list[str]) -> Path | None:
        """
        Finds a matching path from common root directories based on the provided patterns.

        This method checks a predefined set of common root directories and attempts
        to find a match with any of the patterns provided in the `globs` parameter.
        If a matching path is found, it is returned; otherwise, `None` is returned.

        Parameters:
        globs: list[str]
            A list of glob patterns to match against the common root directories.

        Returns:
        Path | None
            The first matching path found in the common root directories, or `None`
            if no matches are found.
        """
        pass

    def best_of(self, *candidates: Path | None, b, c) -> Path | None:
        """
        Determines the best option among the provided candidates based on certain criteria.

        This function evaluates multiple candidate paths based on some logic and
        returns the most optimal one or None if no suitable candidate is found.

        Parameters:
            candidates (Path | None): A variable-length argument of candidate paths
                to be evaluated. Can include None values.
            b: Additional argument affecting the evaluation (type to be inferred).
            c: Another argument influencing the decision-making process (type to
                be inferred).

        Returns:
            Path | None: The most optimal path selected from the candidates or None
            if no valid candidates are determined.

        """
        pass

    def resolve_shortcut(self, path: Path) -> Path | None:
        pass
