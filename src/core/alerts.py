"""Alert configuration and computation for Q-Link.

The alert levels depend on a configurable QBER threshold (default 0.11).
NORMAL   : QBER < 0.8 * threshold
WARNING  : 0.8 * threshold <= QBER < threshold
ABORT    : QBER >= threshold
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass


class AlertLevel(str, Enum):
    """Possible alert states for a QKD run."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    ABORT = "ABORT"


@dataclass
class AlertConfig:
    """Configuration for alert thresholds.

    Attributes
    ----------
    qber_threshold: float
        Base QBER threshold (default 0.11).
    """
    qber_threshold: float = 0.11

    @property
    def warning_boundary(self) -> float:
        return 0.8 * self.qber_threshold


def compute_alert(qber: float, config: AlertConfig = None) -> AlertLevel:
    """Return the appropriate alert level for a given QBER.

    Parameters
    ----------
    qber: float
        Estimated quantum bit error rate (0-1).
    config: AlertConfig, optional
        Custom configuration; if ``None`` the defaults are used.

    Returns
    -------
    AlertLevel
        ``NORMAL``, ``WARNING`` or ``ABORT``.
    """
    cfg = config or AlertConfig()
    if qber >= cfg.qber_threshold:
        return AlertLevel.ABORT
    if qber >= cfg.warning_boundary:
        return AlertLevel.WARNING
    return AlertLevel.NORMAL
