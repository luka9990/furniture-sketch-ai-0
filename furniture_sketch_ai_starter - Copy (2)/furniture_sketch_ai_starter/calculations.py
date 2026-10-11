from __future__ import annotations
from typing import Any
import pandas as pd

PART_COLUMNS = ["name","quantity","length_mm","width_mm","thickness_mm","material","confidence","notes"]

def parts_to_dataframe(analysis: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame(analysis.get("parts", []))
    for col in PART_COLUMNS:
        if col not in df.columns: df[col] = None
    df = df[PART_COLUMNS].copy()
    for col in ["quantity","length_mm","width_mm","thickness_mm"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def validate_parts(df: pd.DataFrame) -> list[str]:
    warnings = []
    for idx, row in df.iterrows():
        name = str(row.get("name") or f"Red {idx+1}")
        q = row.get("quantity")
        if pd.isna(q) or q < 1 or int(q) != q:
            warnings.append(f"{name}: količina mora biti cijeli broj najmanje 1.")
        for col, label in [("length_mm","dužinu"),("width_mm","širinu"),("thickness_mm","debljinu")]:
            val = row.get(col)
            if pd.isna(val) or val <= 0: warnings.append(f"{name}: provjeri {label} (mm).")
        if str(row.get("confidence","")).lower() == "low":
            warnings.append(f"{name}: nisko AI povjerenje — ručno provjeri mjere.")
    return warnings

def add_area_and_volume(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["quantity","length_mm","width_mm","thickness_mm"]: out[c] = pd.to_numeric(out[c], errors="coerce")
    out["total_area_m2"] = out["quantity"] * out["length_mm"] * out["width_mm"] / 1_000_000
    out["total_volume_m3"] = out["quantity"] * out["length_mm"] * out["width_mm"] * out["thickness_mm"] / 1_000_000_000
    return out

def estimate_board_cost(df: pd.DataFrame, price_per_m2: float) -> float:
    return float(add_area_and_volume(df)["total_area_m2"].fillna(0).sum() * price_per_m2)

def export_cut_list_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")
