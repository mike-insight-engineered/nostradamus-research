"""Nostradamus Research — Milestone 1: Historical Translation Calibration.

This package provides the software foundation for calibrating AI translation of
sixteenth-century French and Renaissance Latin into modern French and English.
It deliberately separates three quality dimensions:

* QC1 — fidelity of transcription to historical source witnesses;
* QC2 — fidelity of translation to the historical language;
* QC3 — evidential strength of later interpretations (architecture only).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nostradamus-research")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
