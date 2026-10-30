"""Dataset loader for local satellite QKD dataset.

Source: Zenodo 10.5281/zenodo.14054879 (CC BY 4.0)
Type: MODELED data (DV_Protocol = Decoy-BB84, ENT_protocol = BBM92)
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict
import numpy as np
import pandas as pd
from scipy.io import loadmat

from src.data.schema import COMMON_COLUMNS, validate_dataset_dataframe


DEFAULT_DATA_DIR = r"C:\Projects\QLink\data\raw\satellite"


def _load_dv_protocol(base_dir: str, subsample_factor: int = 1) -> List[Dict]:
    """Load Decoy-BB84 dataset from DV_Protocol (GEO, LEO, MEO)."""
    dv_dir = os.path.join(base_dir, "DV_Protocol")
    if not os.path.isdir(dv_dir):
        return []

    records: List[Dict] = []
    orbits = [("1_GEO", "GEO", "satellite_geo"),
              ("1_LEO", "LEO", "satellite_leo"),
              ("1_MEO", "MEO", "satellite_meo")]

    for folder_name, orbit_label, link_type in orbits:
        orbit_path = os.path.join(dv_dir, folder_name)
        if not os.path.isdir(orbit_path):
            continue

        qber_file = os.path.join(orbit_path, "QBER.mat")
        skr_file = os.path.join(orbit_path, "SKR.mat")
        
        # LinkLoss file name varies slightly in LEO
        ll_file = os.path.join(orbit_path, "LinkLoss_UC1.mat" if orbit_label == "LEO" else "LinkLoss.mat")
        elev_file = os.path.join(orbit_path, "elev_naxos.mat" if orbit_label == "LEO" else "elevation_angle_naxos.mat")

        if not (os.path.exists(qber_file) and os.path.exists(skr_file)):
            continue

        qber_mat = loadmat(qber_file)["QBER"]
        skr_mat = loadmat(skr_file)["SKR"]
        ll_mat = loadmat(ll_file)["LinkLoss"] if os.path.exists(ll_file) else None
        elev_mat = loadmat(elev_file)["elevation_angle"] if os.path.exists(elev_file) else None

        n_rows, n_cols = qber_mat.shape

        # In LEO, skip heavily unpopulated below-horizon timesteps (-inf loss) or subsample
        step = subsample_factor
        if orbit_label == "LEO" and step < 5:
            step = 5  # keep memory and UI fast

        for r_idx in range(0, n_rows, step):
            elev_val = float(elev_mat[r_idx, 0]) if elev_mat is not None else None
            
            # If elevation is 0 or negative, satellite is below horizon
            if elev_val is not None and elev_val <= 0.0:
                continue

            for c_idx in range(n_cols):
                q = float(qber_mat[r_idx, c_idx])
                s = float(skr_mat[r_idx, c_idx])
                loss = float(ll_mat[r_idx, c_idx]) if ll_mat is not None else np.nan

                # Skip completely invalid or -inf / inf loss points
                if np.isneginf(loss) or np.isposinf(loss) or np.isnan(q):
                    continue

                # Loss in dB (store positive magnitude e.g. 45.8 dB)
                loss_db = abs(loss) if np.isfinite(loss) else np.nan
                qber_clean = max(0.0, min(1.0, q))

                if qber_clean >= 0.11:
                    outcome = "ABORT"
                elif s > 0:
                    outcome = "SECURE"
                else:
                    outcome = "NO_KEY"

                records.append({
                    "session_id": f"Decoy-BB84_{orbit_label}_r{r_idx}_ch{c_idx}",
                    "protocol": "Decoy-BB84",
                    "link_type": link_type,
                    "orbit": orbit_label,
                    "elevation_deg": elev_val,
                    "distance_km": None,  # satellite links have no invented distance
                    "link_loss_db": round(loss_db, 2),
                    "qber": round(qber_clean, 4),
                    "key_rate": round(max(0.0, s), 2),
                    "outcome": outcome,
                    "data_source": "modeled",
                })

    return records


def _load_ent_protocol(base_dir: str, subsample_factor: int = 5) -> List[Dict]:
    """Load BBM92 entanglement dataset from ENT_protocol."""
    ent_dir = os.path.join(base_dir, "ENT_protocol")
    if not os.path.isdir(ent_dir):
        return []

    qber_file = os.path.join(ent_dir, "QBER_ent_Helmos_Matera.mat")
    skr_file = os.path.join(ent_dir, "SKR_ent_Helmos_Matera.mat")
    ll_h_file = os.path.join(ent_dir, "LINKLOSS_HELMOS.mat")
    ll_m_file = os.path.join(ent_dir, "LINKLOSS_MATERA.mat")
    elev_h_file = os.path.join(ent_dir, "elev_helmos.mat")

    if not (os.path.exists(qber_file) and os.path.exists(skr_file)):
        return []

    qber_mat = loadmat(qber_file)["QBER"]
    skr_mat = loadmat(skr_file)["SKR"]
    ll_h = loadmat(ll_h_file)["LinkLoss1"] if os.path.exists(ll_h_file) else None
    ll_m = loadmat(ll_m_file)["LinkLoss2"] if os.path.exists(ll_m_file) else None
    elev_h = loadmat(elev_h_file)["elev1"] if os.path.exists(elev_h_file) else None

    records: List[Dict] = []
    n_rows, n_cols = qber_mat.shape

    step = max(5, subsample_factor)
    for r_idx in range(0, n_rows, step):
        elev_val = float(elev_h[r_idx, 0]) if elev_h is not None else None
        if elev_val is not None and elev_val <= 0.0:
            continue

        l1 = float(ll_h[r_idx, 0]) if ll_h is not None else np.nan
        l2 = float(ll_m[r_idx, 0]) if ll_m is not None else np.nan

        if np.isneginf(l1) or np.isneginf(l2):
            continue

        # Combined / representative link loss
        valid_losses = [abs(x) for x in (l1, l2) if np.isfinite(x)]
        avg_loss = float(np.mean(valid_losses)) if valid_losses else np.nan

        for c_idx in range(n_cols):
            q = float(qber_mat[r_idx, c_idx])
            s = float(skr_mat[r_idx, c_idx])

            if np.isnan(q):
                continue

            qber_clean = max(0.0, min(1.0, q))
            if qber_clean >= 0.11:
                outcome = "ABORT"
            elif s > 0:
                outcome = "SECURE"
            else:
                outcome = "NO_KEY"

            records.append({
                "session_id": f"BBM92_ENT_r{r_idx}_ch{c_idx}",
                "protocol": "BBM92",
                "link_type": "satellite_entanglement",
                "orbit": "LEO-Constellation",
                "elevation_deg": elev_val,
                "distance_km": None,
                "link_loss_db": round(avg_loss, 2) if np.isfinite(avg_loss) else np.nan,
                "qber": round(qber_clean, 4),
                "key_rate": round(max(0.0, s), 2),
                "outcome": outcome,
                "data_source": "modeled",
            })

    return records


def load_satellite_dataset(data_dir: str = DEFAULT_DATA_DIR, subsample_factor: int = 2) -> pd.DataFrame:
    """Load and unify all satellite QKD modeled datasets into common schema."""
    dv_records = _load_dv_protocol(data_dir, subsample_factor=subsample_factor)
    ent_records = _load_ent_protocol(data_dir, subsample_factor=subsample_factor)

    all_records = dv_records + ent_records
    if not all_records:
        df = pd.DataFrame(columns=COMMON_COLUMNS)
    else:
        df = pd.DataFrame(all_records)

    return validate_dataset_dataframe(df)
