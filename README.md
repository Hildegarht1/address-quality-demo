# address-quality-demo
Address Quality &amp; Geocoding Demo
Live demo: https://quality-address-geocoding.streamlit.app/  

Short description
This mini project demonstrates a small ETL pipeline for address normalization and geocoding, plus an interactive Streamlit dashboard for KPI monitoring and failure analysis. It is a compact, shareable demo designed for hiring portfolios (data engineering / BI / geospatial roles).

Current run metrics (live)
- Sample size: 198 addresses
- Geocode success: 179
- Success rate: 90.4%

What the demo shows
- Address normalization and simple quality scoring
- Geocoding with caching to avoid repeated queries
- An interactive Streamlit dashboard with:
  - KPI cards (total, success count, success rate)
  - Map view of geocoded points
  - Table of failed / low-quality addresses and filters
- Simple ETL output (Parquet) that can be reused in analysis pipelines

Tech stack
- Python (pandas, geopy, pyarrow)
- Geospatial: geopandas, folium / plotly
- Dashboard: Streamlit (deployed)
- Storage / ETL artifacts: Parquet
- Optional: OpenCage / Google V3 providers (via geopy) for higher coverage

Quickstart (local)
1. Clone the repo
   git clone https://github.com/Hildegarht1/address-quality-demo
   cd address-quality-demo

2. Create & activate a virtual environment
   python -m venv venv
   # macOS / Linux
   source venv/bin/activate
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1

3. Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt

   Note: geopandas may be easier to install with conda. If pip install fails for geopandas, use conda:
   conda create -n geodemo python=3.10
   conda activate geodemo
   conda install -c conda-forge geopandas folium

4. (Optional) Use the larger sample
   - Replace `data/addresses_sample.csv` with `data/addresses_sample_large.csv`
   OR
   - Run the generator:
     python scripts/generate_addresses.py --n 198

5. Run the ETL geocode script
   python notebooks/01_geocode.py
   This produces: outputs/addresses_clean.parquet, outputs/addresses_preview.csv, outputs/geocode_cache.json

6. Run the Streamlit app
   streamlit run app.py
   Open the shown local URL to inspect the dashboard.

Available scripts & helper workflows
- scripts/generate_addresses.py: creates a synthetic multi-country sample for demos.
- scripts/retry_failed_geocoding.py: retries failed addresses using structured component queries and optional multi-provider fallbacks (OpenCage, Google). Set OPENCAGE_KEY or GOOGLE_KEY as env vars to enable those providers.

Deployment notes & secrets
- When deploying to Streamlit Community Cloud, add API keys as secrets (OpenCage/Google) if you want multi-provider fallback enabled on the server.
- The free Nominatim provider (via geopy) enforces strict rate limits; respect usage policy. For larger demos or production use switch to a paid provider.
- outputs/metrics.json is written on each app run and contains:
  {
    "total": <int>,
    "success": <int>,
    "success_rate_pct": <float>,
    "failed_count": <int>
  }
  This file makes it easy to surface run metrics in CI or in the repo after a run.

  Failure analysis & next steps
- Current failures are mostly:
  - Placeholder or clearly invalid addresses (e.g., "Invalid address example, Nowhere")
  - Addresses missing city/postcode or with local formats (e.g., Japanese chome)
  - Regional gaps for free providers (Nominatim) for some countries
- Recommended improvements (next tasks):
  1. Add multi-provider fallback (OpenCage / Google / Mapbox) to increase coverage.
  2. Integrate libpostal (via `postal`) for robust parsing/normalization (native libpostal install required).
  3. Classify & mark unresolvable addresses (PO boxes, insufficient context) to avoid wasting API calls.
  4. Optionally store results in cloud (S3) and use DBT for a transformation layer.

Contact / author
Hilda Amadu — github.com/Hildegarht1 — linkedin.com/in/hilda-amadu
