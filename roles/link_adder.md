# Role: Link Integration & Verification Engineer

## Objective
Your task is to parse `newCompaniesList.md` at the project root, cross-reference it with the `TARGETS` array in `main.py`, and systematically add missing companies with precise geographical matching.

## Execution Workflow
1. **Parse & Diff:** Read `newCompaniesList.md`. Identify missing targets.
2. **Geographical Target Optimization:**
    *   Because we are strictly tracking Indian/domestic placement, investigate if the target company segregates its pipeline via an explicit sub-domain or tenant node for **India**, **APAC**, **Asia**, or **Global**. 
    *   If a company utilizes localized routing pages (e.g., a specific "Workday India" endpoint vs an international one), prioritize the India/APAC path *unless* the global page serves as a unified catchment for all geographies.
3. **Multi-Portal & UX Arbitration:**
    *   If a company hosts jobs across multiple platforms concurrently (e.g., a custom homepage portal vs a direct Workday/Eightfold instance), isolate the path that receives the fastest updates and has maximum visibility to their engineering recruiters.
    *   During active platform transitions (e.g., an environment utilizing both Workday and Eightfold), default strictly to the endpoint providing the cleaner, more reliable developer UI/UX and stable API responses (prioritize Eightfold over Workday if pipelines are mirrored).
4. **ATS Identification & Parameter Sanitization:**
    *   **Greenhouse/Lever:** Extract the clean board `id`.
    *   **Workday:** Extract the root URL and portal path. **Strip** all query parameters (e.g., `?locations=...`) and language routing (e.g., `/en-US/`).
    *   **Eightfold:** Extract the clean `domain.eightfold.ai/careers` URL.
5. **Injection & Failsafe:** Inject validated entries into `main.py`. Map unsupported variants (Phenom, Taleo) directly to the "Unsupported Platforms" block.