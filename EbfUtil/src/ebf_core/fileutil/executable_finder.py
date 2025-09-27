from pathlib import Path


class ExecutableFinder:
    def find_on_system_path(self, executable_names: list[str]) -> Path | None:
        """
        Find the first executable in the given list that exists on the system's PATH.

        This method iterates through the provided list of executable names and searches
        for the first executable that exists in directories specified in the system's
        PATH environment variable. If a match is found, the path to the executable is
        returned. If no executable is found, None is returned.

        Args:
            executable_names (list[str]): A list of executable names to search for on the
            system's PATH Extensions are ignored.

        Returns:
            Path | None: The absolute path to the found executable, or None if no
            executable is found.
        """
        pass

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
