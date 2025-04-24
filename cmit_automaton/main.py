# -*- coding: utf-8 -*-


"""
─────────────────────────────────────────────────────────────
CMIT Scraper: Main Execution Flow
Author: AQMP
Description: Automates data extraction from the CMIT portal
						 using structured configuration and Selenium-based 
						 scraping.
─────────────────────────────────────────────────────────────
"""

#────────── Base Python imports ──────────────────────────────────────────────────────────────────────────────
import json
import json
from pathlib import Path
from datetime import datetime

#────────── Project-specific imports (directly from this project's source code) ──────────────────────────────
from databuild import data
from webdriver_factory import DriverContext
from utils import (                           
    wait_for_page_load,
    extract_measure_name,
    extract_table_data,
    extract_cmit_metadata,
    extract_cmit_ID,
    flatten_results,
)


# ------ Page Configuration ---
PAGE_INFO = json.loads(Path("cmit_pages.json").read_text())

# ------ Output Configuration ---
OUTFILE = f"cmit_scrape_flat_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

# ------ Logging Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ------ Scraping Loop ---
def crawl():
    results = []
    with DriverContext(headless=True) as driver:
        for i, (cmit_id, variant_id) in enumerate(data.items(), 1):
            logging.info("Scraping %s (%s/%s)", cmit_id, i, len(data))
            record = {"CMIT ID": cmit_id, "Variant ID": variant_id}
            try:
                for page_name, page_info in PAGE_INFO["page"].items():
                    url = page_info["url"].format(variantId=variant_id)
                    driver.get(url)
                    driver.refresh()

                    wait_for_page_load(driver)

                    if page_name == "Properties":
                        record["Measure Name"] = extract_measure_name(driver)
                        record["Metadata"] = extract_cmit_metadata(driver)

                    record[page_name] = extract_table_data(
                        driver, css_selector=page_info["css_selector"]
                    )

            except Exception as err:
                logging.error(" Failed on %s: %s", cmit_id, err, exc_info=True)
            results.append(record)
    return results

if __name__ == "__main__":
    flattened = flatten_results(crawl(), OUTFILE)
    logging.info(" Export complete → %s", OUTFILE)
