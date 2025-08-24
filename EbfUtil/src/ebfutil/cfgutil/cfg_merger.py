from typing import Mapping, Any


class ConfigMerger:
    """Centralizes deep-merge for configs.

    src overrides tgt:
      • Dicts deep-merge
      • Lists/scalars replace

    Notes:
      - If tgt is None, returns dict(src) or {}.
      - If src is None, returns dict(tgt).
      - Does not mutate inputs.
    """

    @staticmethod
    def deep(tgt: Mapping[str, Any] | None, src: Mapping[str, Any] | None) -> dict[str, Any]:
        if tgt is None:
            return dict(src or {})
        if src is None:
            return dict(tgt)

        result: dict[str, Any] = dict(tgt)  # copy; do not mutate tgt
        for k, v in src.items():
            if isinstance(v, Mapping) and isinstance(result.get(k), Mapping):
                result[k] = ConfigMerger.deep(result[k], v)  # type: ignore[arg-type]
            else:
                result[k] = v
        return result
