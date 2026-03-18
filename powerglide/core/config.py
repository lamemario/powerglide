"""Read powerglide.toml and expose settings with sensible defaults."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]


def _find_config() -> Path | None:
    """Walk up from CWD looking for powerglide.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "powerglide.toml"
        if candidate.is_file():
            return candidate
    return None


def _load_config() -> dict:
    path = _find_config()
    if path is None:
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


_raw = _load_config()


class Settings:
    def __init__(self, raw: dict) -> None:
        self._raw = raw

    @property
    def db_path(self) -> Path:
        rel = self._raw.get("database", {}).get("path", "data/app.db")
        path = Path(rel)
        if not path.is_absolute():
            config_file = _find_config()
            root = config_file.parent if config_file else Path.cwd()
            path = root / path
        return path

    @property
    def acute_window(self) -> int:
        return int(self._raw.get("acwr", {}).get("acute_window", 7))

    @property
    def chronic_window(self) -> int:
        return int(self._raw.get("acwr", {}).get("chronic_window", 28))

    @property
    def acwr_undertrained_max(self) -> float:
        return float(self._raw.get("acwr", {}).get("undertrained_max", 0.80))

    @property
    def acwr_optimal_max(self) -> float:
        return float(self._raw.get("acwr", {}).get("optimal_max", 1.30))

    @property
    def acwr_caution_max(self) -> float:
        return float(self._raw.get("acwr", {}).get("caution_max", 1.50))

    @property
    def default_unit(self) -> str:
        return self._raw.get("defaults", {}).get("unit", "kg")

    @property
    def date_format(self) -> str:
        return self._raw.get("defaults", {}).get("date_format", "DD/MM/YY")

    @property
    def volume_coeff_primary(self) -> float:
        return float(self._raw.get("volume_coefficients", {}).get("primary", 1.0))

    @property
    def volume_coeff_secondary(self) -> float:
        return float(self._raw.get("volume_coefficients", {}).get("secondary", 0.5))

    @property
    def volume_coeff_stabilizer(self) -> float:
        return float(self._raw.get("volume_coefficients", {}).get("stabilizer", 0.25))


settings = Settings(_raw)
