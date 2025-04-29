## Standard Operating Procedure (SOP)  
### Automated Extraction of CMS Measures from the CMIT Portal

---

| **Version** | **Date** | **Author** | **Change Log** |
|-------------|----------|------------|----------------|
| 1.0 | 2025-04-24 | ???? | Initial release |

---

### 1. Purpose  
Provide a repeatable procedure for installing, configuring, and running an automated Selenium-based scraper that collects metadata and table data for every CMS Healthcare Quality Measure published in the CMIT portal.

---

### 2. Scope  
This SOP applies to all team members who need to:

* Assemble or refresh the master CMIT dataset.  
* Extract Properties, Characteristics, Cascade of Meaningful Measures, Groups, and Reporting Status for selected CMIT IDs.  
* Flatten results to an Excel workbook for analysis.

---

### 3. Roles & Responsibilities  

| Role | Responsibility |
|------|----------------|
| **Data Engineer** | Maintain codebase, update `requirements.txt` and `settings.yaml`, review scrape output. Store final Excel in Databricks environment; schedule production runs if needed. |
| **Project Lead** | Approve changes to SOP; ensure compliance with CMS website terms of use. |

---

### 4. Prerequisites  

1. **Python 3.8 +** installed.<br>
2. **Google Chrome** installed (matching chromedriver version when one is used).  
3. **Git** access to the `cmit_automaton` repository.

---

### 5. Installation & First-Time Setup  

#### 5.1 Clone the repository  
```bash
git clone https://…/cmit_automaton.git
cd cmit_automaton
```

#### 5.2 Install dependencies  
```bash
python -m pip install -r requirements.txt
```
*(If desired, run `python bootstrap.py`, which installs any missing packages automatically.)*

#### 5.3 Configure settings  

Edit **`settings.yaml`** in the project root:

```yaml
chromedriver_path: "C:/Path/To/chromedriver.exe"   # leave blank to auto-download
output_dir: "C:/CMIT/outputs"                      # optional
```

---

### 6. Preparing Input Data  

1. Open **`target.txt`** and list one **CMIT ID** per line (example):  
   ```
   01018-01-C-HIQR
   01499-01-C-HVBP
   ```  
2. Save the file. The scraper will look up matching `variant_id`s from **`cmit_variant_relationship.xlsx`** automatically.

---

### 7. Running the Scraper  

```bash
python main.py
```

**What happens:**

1. `databuild.py` builds `{cmit_id: variant_id}` from the Excel mapping and `target.txt`.  
2. `webdriver_factory.get_driver()` launches Chrome headless, creating or downloading `chromedriver` if missing.  
3. `main.py` iterates over every CMIT/Variant pair, opens each of the five CMIT tabs, waits for Angular to finish rendering, and extracts:  
   * Measure Name & master Metadata  
   * Section tables (Properties, Characteristics, etc.)  
4. Results are flattened via `flatten_results()` and saved as  
   ```
   cmit_scrape_flat_YYYYMMDD_HHMMSS.xlsx
   ```  
   in the project directory (or `output_dir` from `settings.yaml`).

---

### 8. Post-Processing & Storage  

* Verify row counts and spot-check at least 5 random measures against the CMIT UI.  
* Move the Excel file to the shared data repository (`<project>/raw/cmit/YYYYMMDD/`).  
* Update downstream dashboards or data pipelines as required.

---

### 9. Error Handling & Troubleshooting  

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| `FileNotFoundError: Chromedriver path not found` | `chromedriver_path` not set and auto-download failed | 1) Install `webdriver-manager`  `pip install webdriver-manager` 2) Or specify a local path in `settings.yaml`. |
| Browser opens but remains blank | CMIT site changed loader selector | Update `wait_for_page_load` spinner CSS in `utils.py`. |
| Rows missing in output | CMIT ID not in mapping Excel | Add the missing ID/variant pair to `cmit_variant_relationship.xlsx`. |
| `selenium.common.exceptions.*` | Out-of-date driver vs. Chrome | Re-run with auto-download, or manually update chromedriver. |

---

### 10. Maintenance  

| Task | Frequency | Owner |
|------|-----------|-------|
| Refresh `cmit_variant_relationship.xlsx` from CMS | ???? | ???? |
| Verify scraper after CMIT UI updates | After major CMS releases | ???? |
| Pin library versions in `requirements.txt` | As needed | ???? |

