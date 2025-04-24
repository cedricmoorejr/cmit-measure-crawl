## **Data Extraction from CMIT CMS Healthcare Quality Measures Portal**

### **Objective**
The purpose of this procedure is to extract structured metadata and tabular data from the CMIT CMS website for all publicly accessible Healthcare Quality Measures. This information is critical for internal analysis and reporting related to CMS quality programs.

---

### **Scope**
This SOP covers the systematic crawling and data extraction from five key web sections for each quality measure accessible via the CMIT portal. The process involves dynamic page interaction due to the Angular-based nature of the site.

---

### **Data Source**
- **Website:** [https://cmit.cms.gov/cmit/](https://cmit.cms.gov/cmit/)
- **Navigation:** Each measure is accessible via a `variantId`, and each relevant data section is accessed by appending a `sectionNumber` in the URL.

---

### **Target Sections Per Measure**
For every valid `variantId`, data will be extracted from the following sections:

| Section | Name                          | `sectionNumber` |
|---------|-------------------------------|-----------------|
| 1       | Properties                    | 1               |
| 2       | Characteristics               | 3               |
| 3       | Cascade of Meaningful Measures| 4               |
| 4       | Groups                        | 5               |
| 5       | Reporting Status              | 7               |

---

### **Challenges & Considerations**
- The CMIT portal is built using Angular, a Single Page Application (SPA) framework.
- Traditional HTTP-based scraping is ineffective due to dynamic content rendering and session-protected APIs.
- A browser automation tool (e.g., Selenium) is required to render and interact with content.

---

### **Implementation Plan**

1. **Automation Tooling**
   - Utilize Python and Selenium WebDriver to simulate user interaction and extract rendered HTML content.
   - Apply `WebDriverWait` to ensure content is fully loaded before extraction.

2. **Page Detection Logic**
   - Iterate through `variantId` values from `0` to `9296`.
   - Attempt to load the Properties page (`sectionNumber=1`) for each `variantId`.
   - Log whether the page is valid (HTTP 200) or invalid (HTTP 404 or rendering error).

3. **Data Extraction Logic**
   - If a measure is valid, navigate to all five sections listed above.
   - Extract:
     - Common metadata (e.g., Measure ID, Program, Status) displayed consistently in the top-left section.
     - Tabular data from each section using the following DOM structure:
       - `div.row.margin-top-10` under these root elements:
         - Properties: `app-measure-properties`
         - Characteristics: `app-characteristics`
         - Cascade: `app-cascade`
         - Groups: `app-groups`
         - Reporting Status: `app-programs`

4. **Output and Logging**
   - Store extracted data in a structured dataset (e.g., CSV or database).
   - Maintain a log of:
     - Valid and invalid `variantId`s
     - Extraction errors
     - Section-specific success/failure

5. **Post-Processing**
   - Construct a lookup table mapping `variantId` to `Measure ID` and associated metadata.
   - Optionally, derive mappings from `variantId` to program name, status, and other measure attributes.

---

### **Tools and Dependencies**
- Python 3.x
- Selenium WebDriver
- ChromeDriver or equivalent browser driver
- Pandas (for data handling)
- Logging library (e.g., `logging` or `loguru`)

---

### **Security & Compliance**
- Do not bypass authentication or scrape restricted APIs.
- Respect rate limits and server resources during automated scraping.
- Follow institutional and legal guidelines for web data collection.
