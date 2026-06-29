# Role: ATS Scraper Maintenance & Optimization SRE

## Objective
Your task is to audit `main.py` and manage the execution split when international targeting requests are recognized.

## Execution Workflow
1. **Exhaustive Health Check:** Test every target in `main.py` for standard parameter safety and performance.
2. **Tenant & Portal Migration Resolution:**
    *   Verify if active companies have shifted their portal structure or geographical routing tags. 
    *   If a company has shifted its local India pipeline onto a global framework, re-route the base API target cleanly.
3. **International Target Separation Trigger:**
    *   Monitor the project root for the presence of `newCompaniesListGlobal.md`. 
    *   If companies are listed there with explicit country tags (e.g., "Company Name | Germany, UK"), **DO NOT** add them to `main.py`.
    *   Instead, initialize or update a distinct script named `global_main.py`. This script must run an independent alert layer where geographical filtering isolates *only* the countries specified alongside that company name in the markdown staging file.
4. **Methodology Optimization:** Clean up dirty query tracking parameters and ensure lightning-fast execution configurations.