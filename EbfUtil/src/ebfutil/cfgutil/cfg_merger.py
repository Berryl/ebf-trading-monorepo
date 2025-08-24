from __future__ import annotations

from typing import Any, Mapping


class ConfigMerger:
    """Centralizes deep-merge behavior.

    Why: keep merge logic reusable/testable; src overrides tgt.
    Dicts deep-merge; lists/scalars replace.
    """

    @staticmethod
    def deep(tgt: dict[str, Any] | None, src: Mapping[str, Any] | None) -> dict[str, Any]:
        if not tgt:
            return dict(src or {})
        if not src:
            return tgt
        for k, v in src.items():
            if isinstance(v, Mapping) and isinstance(tgt.get(k), Mapping):
                tgt[k] = ConfigMerger.deep(dict(tgt[k]), v)  # type: ignore[arg-type]
            else:
                tgt[k] = v
        return tgt
