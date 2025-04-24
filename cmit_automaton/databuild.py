# -*- coding: utf-8 -*-

"""
Module
-------

Loads a master CMIT variant mapping from Excel and filters it
based on a user-provided file of CMIT IDs.
Returns a dictionary: {cmit_id: variant_id}
"""


#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import pandas as pd

def build_data_dict(
    cmit_excel_path="C:/PythonCustomModules/cmit_automaton/cmit_automaton/cmit_variant_relationship.xlsx",
    user_input_path="C:/PythonCustomModules/cmit_automaton/cmit_automaton/target.txt"
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
    # Load master Excel mapping
    df_master = pd.read_excel(cmit_excel_path)
    df_master.columns = df_master.columns.str.lower().str.strip()

    # Load target CMIT IDs from user input
    try:
        user_ids = pd.read_csv(user_input_path, header=None).squeeze("columns").astype(str).tolist()
    except Exception:
        user_ids = pd.read_excel(user_input_path, header=None).squeeze("columns").astype(str).tolist()

    # Filter master by target CMIT IDs
    filtered = df_master[df_master["cmit_id"].isin(user_ids)]

    # Create mapping {cmit_id: variant_id}, ensuring variant_id is an int
    data_dict = {row["cmit_id"]: int(row["variant_id"]) for _, row in filtered.iterrows()}

    return data_dict


data = build_data_dict()
