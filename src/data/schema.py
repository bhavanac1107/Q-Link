"""Schema definitions for Q-Link standardized datasets.

Defines the common schema and validation models for both modeled and experimental data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


COMMON_COLUMNS = [
    "session_id",
    "protocol",
    "link_type",
    "distance_km",
    "link_loss_db",
    "qber",
    "key_rate",
    "outcome",
    "data_source",
]


@dataclass
class DatasetRecord:
    session_id: str
    protocol: str
    link_type: str
    link_loss_db: float
    qber: float
    key_rate: float
    outcome: str
    data_source: str = "modeled"
    distance_km: Optional[float] = None
    elevation_deg: Optional[float] = None
    orbit: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


def validate_dataset_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that the dataframe conforms to the common schema and sanitize values.

    - Ensures required columns exist.
    - Forces data_source = 'modeled' where missing.
    - Validates QBER range [0.0, 1.0] and drops completely invalid non-numeric rows.
    - Leaves distance_km empty (None/NaN) when missing.
    """
    df = df.copy()
    for col in COMMON_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Enforce data_source
    df["data_source"] = "modeled"

    # Numeric coercion
    df["qber"] = pd.to_numeric(df["qber"], errors="coerce")
    df["link_loss_db"] = pd.to_numeric(df["link_loss_db"], errors="coerce")
    df["key_rate"] = pd.to_numeric(df["key_rate"], errors="coerce")

    # Drop rows where QBER is not a valid number
    valid_mask = df["qber"].notna() & (df["qber"] >= 0.0) & (df["qber"] <= 1.0)
    df = df[valid_mask].reset_index(drop=True)

    return df
