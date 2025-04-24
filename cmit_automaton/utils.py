# -*- coding: utf-8 -*-


#────────── Base Python imports ──────────────────────────────────────────────────────────────────────────────
import logging
import re
from copy import deepcopy

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_page_load(driver, timeout=30):
    """
    Waits for the Angular loading spinner to disappear from the page.

    Params:
    -----------    	
        driver (webdriver): The Selenium WebDriver instance.
        timeout (int): Maximum number of seconds to wait before timing out.

    Returns:
    -----------    	    	
        None
    """
    spinner_locator = (By.CSS_SELECTOR, "span.fa-spinner")
    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element(spinner_locator)
    )
    
def extract_measure_name(driver):
    """
    Extracts the name of the measure displayed at the top of the page.

    Params:
    -----------    	    	
        driver (webdriver): The Selenium WebDriver instance.

    Returns:
    -----------    	    	
        str: The extracted measure name as displayed in the header.
    """
    # Locate the element using the CSS selector
    element = driver.find_element(By.CSS_SELECTOR, "div.row.margin-top-10.padding-bottom-15 h1 span")

    # Extract the text
    return element.text
    
# def extract_table_data(css_selector):
#     """
#     Extracts labeled table data from a given section of the CMIT page.
# 
#     Params:
#     -----------    	    	
#         css_selector (str): The CSS selector used to locate the target data rows.
# 
#     Returns:
#     -----------    	    	
#         dict: A dictionary of {label: value} pairs extracted from the page,
#               where values may be direct text or a hyperlink if available.
#     """
#     site_data = {}
#     rows = driver.find_elements(By.CSS_SELECTOR, css_selector)
# 
#     for row in rows:
#         try:
#             label_element = row.find_element(By.CSS_SELECTOR, "div.col-md-3")
#             value_element = row.find_element(By.CSS_SELECTOR, "div.col-md-7")
# 
#             label = label_element.text.strip()
#             value = value_element.text.strip()
# 
#             # If there's a link in the value, capture its href
#             link = value_element.find_elements(By.TAG_NAME, "a")
#             if link:
#                 value = link[0].get_attribute("href")
# 
#             site_data[label] = value if value else "Not Available"
# 
#         except Exception as e:
#             print(f"Failed to process one row: {e}")
# 
#     return site_data

def extract_table_data(driver, css_selector):
    """
    Extracts labeled table data from a given section of the CMIT page.

    Parameters
    ----------
    driver : webdriver
        The Selenium WebDriver instance.
    css_selector : str
        CSS selector used to locate the target data rows.

    Returns
    -------
    dict
        {label: value} pairs, where value may be direct text or a hyperlink.
    """
    site_data = {}
    rows = driver.find_elements(By.CSS_SELECTOR, css_selector)

    for row in rows:
        try:
            label_element = row.find_element(By.CSS_SELECTOR, "div.col-md-3")
            value_element = row.find_element(By.CSS_SELECTOR, "div.col-md-7")

            label = label_element.text.strip()
            value = value_element.text.strip()

            # If there's a link in the value, capture its href
            link = value_element.find_elements(By.TAG_NAME, "a")
            if link:
                value = link[0].get_attribute("href")

            site_data[label] = value if value else "Not Available"

        except Exception as e:
            print(f"Failed to process one row: {e}")

    return site_data


def extract_cmit_metadata(driver):
    """
    Extracts key CMIT metadata fields displayed in the top-left section of the measure page.

    Params:
    -----------    	    	
        driver (webdriver): The Selenium WebDriver instance.

    Returns:
    -----------    	    	
        dict: A dictionary containing extracted metadata values for fields like
              'CMIT Measure ID', 'CMIT ID', 'Measure Type', etc. Returns
              'Not Available' if a field is missing.
    """
    try:
        # Configure logging
        logging.basicConfig(level=logging.INFO)

        # Get all text rows for metadata
        all_text = driver.find_elements(By.CSS_SELECTOR, "span div.row")
        full_text = " | ".join([text.text for text in all_text])

        # Define labels to search for in the text
        labels = [
            "CMIT Measure ID", "CMIT ID", "Measure Type",
            "Date of Information", "Revision", "Program"
        ]
        
        # Dictionary to hold the extracted data
        data = {}

        # Function to extract data using labels
        def extract_data_from_label(text, label):
            start = text.find(label)
            if start == -1:
                return "Not Available"
            start += len(label) + 1  # Start after the label and colon
            end = text.find(" |", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()

        # Extract data for each label
        for label in labels:
            data[label] = extract_data_from_label(full_text, label)

        return data

    except Exception as e:
        logging.error(f"Failed to extract metadata: {e}")
        return None


def extract_cmit_ID(driver):
    """
    Extracts the CMIT ID from the first metadata row using a regex pattern.

    Params:
    -----------    	    	
        driver (webdriver): The Selenium WebDriver instance.

    Returns:
    -----------    	    	
        dict or None: A dictionary containing the 'CMIT ID' if found,
                      or None if extraction fails or the pattern is not matched.
    """
    try:
        # First row (basic metadata)
        first_row = driver.find_elements(By.CSS_SELECTOR, "span div.row.margin-top-10")[0].text

        # Regex pattern to extract all fields allowing empty values.
        pattern = (
            r"CMIT ID:\s*([\w\d-]*)\s*\|\s*"
        )
        match = re.search(pattern, first_row)
        if match:
            # Function to substitute default value if the field is empty
            def safe_value(value):
                return value.strip() if value.strip() else "Not Available"

            data = {
                "CMIT ID": safe_value(match.group(1)),
            }
            return data
        else:
            print("Failed to match pattern - page structure might have changed.")
            return None

    except Exception as e:
        print(f"Failed to extract metadata: {e}")
        return None
       
       
def flatten_results(results, out_path, nested_cols=None):
    """
    Convert the list of CMIT-scrape dicts to a flat DataFrame and save it.

    Params:
    --------
    results : list[dict]
        The list returned by the scraping loop.
    out_path : str or Path
        Destination .xlsx path.
    nested_cols : iterable[str], optional
        Column names that contain nested dicts; they will be expanded.
        Defaults to the known CMIT columns.
    """
    # Safety-copy to avoid mutating caller data
    df = pd.DataFrame(deepcopy(results))

    # Default columns to flatten
    if nested_cols is None:
        nested_cols = [
            "Metadata",
            "Properties",
            "Characteristics",
            "Cascade of Meaningful Measures",
            "Groups",
            "Reporting Status",
        ]

    # Build list of exploded DataFrames
    flat_parts = []
    for col in nested_cols:
        if col not in df:
            continue                      # skip if column missing
        # `errors="ignore"` in case some rows are None / NaN
        flat = (
            pd.json_normalize(df[col].dropna())   # turn dicts → columns
            .add_prefix(f"{col}_")                # add prefix for clarity
        )
        flat_parts.append(flat)
        df = df.drop(columns=col)                 # remove nested col

    # Align indexes and concat
    df_final = pd.concat([df] + flat_parts, axis=1)

    # Persist
    df_final.to_excel(out_path, index=False)
    print(f"Exported {len(df_final)} rows → {out_path}")
       
       

__all__ = [
    "wait_for_page_load",
    "extract_measure_name",
    "extract_table_data",
    "extract_cmit_metadata",
    "extract_cmit_ID",
    "flatten_results"    
]
