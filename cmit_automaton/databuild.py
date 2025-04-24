# -*- coding: utf-8 -*-

"""
Module
-------

Loads a master CMIT variant mapping from Excel and filters it
based on a user-provided file of CMIT IDs.
Returns a dictionary: {cmit_id: variant_id}
"""
#────────── Base Python imports ──────────────────────────────────────────────────────────────────────────────
from pathlib import Path

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import pandas as pd

# Detect project root (folder that contains databuild.py)
BASE_DIR = Path(__file__).resolve().parent


def build_data_dict(
    cmit_excel_path = "cmit_variant_relationship.xlsx",
    user_input_path = "target.txt",
    base_dir: Path = BASE_DIR,
):
    """
    Builds a dictionary mapping CMIT IDs to Variant IDs for scraping.

    Params:
    ----------
    cmit_excel_path : str, optional
        Path to the master Excel file mapping `cmit_id` → `variant_id`.
    user_input_path : str, optional
        Path to user-supplied list of CMIT IDs (one per line or in a column).

    Returns:
    -------
    dict
        Dictionary in the format {cmit_id: variant_id}, limited to user-specified CMIT IDs.

    Notes
    -----
    - The target file can be a .txt, .csv, or .xlsx with one ID per row.
    """
    # Convert to Path objects
    cmit_excel_path = Path(cmit_excel_path)
    user_input_path = Path(user_input_path)

    # Resolve relative paths
    if not cmit_excel_path.is_absolute():
        cmit_excel_path = base_dir / cmit_excel_path
    if not user_input_path.is_absolute():
        user_input_path = base_dir / user_input_path

    df_master = pd.read_excel(cmit_excel_path)
    df_master.columns = df_master.columns.str.lower().str.strip()

    try:
        user_ids = (
            pd.read_csv(user_input_path, header=None)
            .squeeze("columns")
            .astype(str)
            .tolist()
        )
    except Exception:
        user_ids = (
            pd.read_excel(user_input_path, header=None)
            .squeeze("columns")
            .astype(str)
            .tolist()
        )

    filtered = df_master[df_master["cmit_id"].isin(user_ids)]
    return {row["cmit_id"]: int(row["variant_id"]) for _, row in filtered.iterrows()}

data = build_data_dict()
