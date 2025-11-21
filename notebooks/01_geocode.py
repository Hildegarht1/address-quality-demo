# Notebook-style script: 01_geocode.py
# Usage:
# - Run this file cell-by-cell in a Jupyter notebook or execute as a script (it will run top-to-bottom).
# - It reads data/addresses_sample.csv, normalizes and geocodes addresses (uses caching), and writes outputs/addresses_clean.parquet.

import time
import os
from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
from tqdm import tqdm

# --- CONFIG ---
DATA_DIR = Path("data")
OUTPUTS_DIR = Path("outputs")
CACHE_FILE = OUTPUTS_DIR / "geocode_cache.json"
INPUT_CSV = DATA_DIR / "addresses_sample.csv"
OUTPUT_PARQUET = OUTPUTS_DIR / "addresses_clean.parquet"
USER_AGENT = "hilda_geocode_demo"  # change if you like
# Create dirs
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# --- 1. Load data ---
df = pd.read_csv(INPUT_CSV)
df["original_address"] = df["address"].astype(str)
print(f"Loaded {len(df)} rows from {INPUT_CSV}")

# --- 2. Simple normalization function ---
def normalize_address(addr: str) -> str:
    a = str(addr).strip()
    a = a.replace("\n", ", ")
    a = a.replace("  ", " ")
    a = a.lower()
    # Basic replacements (expand as needed)
    a = a.replace("st.", "street")
    a = a.replace("rd.", "road")
    a = a.replace("str.", "strasse")
    return a

df["normalized_address"] = df["original_address"].apply(normalize_address)

# --- 3. Geocoding with caching ---
# Load or init cache
if CACHE_FILE.exists():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

geolocator = Nominatim(user_agent=USER_AGENT, timeout=10)
rate_limiter = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

def geocode_with_cache(addr: str):
    key = addr
    if key in cache:
        return cache[key]
    try:
        location = rate_limiter(addr)
        if location:
            result = {
                "lat": location.latitude,
                "lon": location.longitude,
                "raw": location.raw,
                "success": True,
            }
        else:
            result = {"lat": None, "lon": None, "raw": None, "success": False}
    except Exception as e:
        result = {"lat": None, "lon": None, "raw": None, "success": False, "error": str(e)}
    # write-back to cache immediately to avoid re-query on reruns
    cache[key] = result
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return result

# Apply geocoding (small dataset; for larger sets, batch and follow provider limits)
lat_list, lon_list, success_list = [], [], []
for addr in tqdm(df["normalized_address"].fillna("").tolist()):
    res = geocode_with_cache(addr)
    lat_list.append(res.get("lat"))
    lon_list.append(res.get("lon"))
    success_list.append(res.get("success", False))

df["lat"] = lat_list
df["lon"] = lon_list
df["geocode_success"] = success_list

# --- 4. Quality scoring (simple example) ---
# Example: quality score 1 if success and raw has 'importance' or similar, else 0.5 for success without extra info.
def compute_quality(raw):
    if not raw:
        return 0.0
    # tune this as needed; geopy Nominatim returns limited details
    return 1.0 if raw.get("importance") else 0.8

df["match_score"] = df.apply(lambda r: compute_quality(r.get("raw") if isinstance(r.get("raw"), dict) else None), axis=1)

# --- 5. KPIs ---
total = len(df)
success_count = df["geocode_success"].sum()
success_rate = (success_count / total) * 100 if total > 0 else 0.0
print(f"Total addresses: {total}, Geocode success: {success_count}, Success rate: {success_rate:.2f}%")

# Regional aggregation example if 'city' or 'postcode' present
if "city" in df.columns:
    region_rates = df.groupby("city")["geocode_success"].agg(["count", "sum"])
    region_rates["success_rate_pct"] = (region_rates["sum"] / region_rates["count"]) * 100
    print(region_rates.reset_index().head())

# --- 6. Save cleaned dataset as parquet ---
df.to_parquet(OUTPUT_PARQUET, index=False)
print(f"Saved cleaned dataset to {OUTPUT_PARQUET}")

# --- 7. Output summary CSV for quick inspection ---
df.head(20).to_csv(OUTPUTS_DIR / "addresses_preview.csv", index=False)
print("Wrote preview CSV to outputs/addresses_preview.csv")