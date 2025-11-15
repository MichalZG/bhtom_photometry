# -*- coding: utf-8 -*-
"""BHTOM Dataproduct list and download cpcs dat file

Script for downloading and processing photometric data from BHTOM.
"""

import json
import requests
from typing import Optional, List, Dict, Tuple
import pandas as pd
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
from astropy.time import Time
import numpy as np
import os

# Load API credentials and configuration from environment variables or config file
def load_api_config():
    """Load API configuration and credentials from environment variables or config.py file."""
    # Try to load from environment variables first
    api_base_url = os.getenv('BHTOM_API_BASE_URL')
    api_token = os.getenv('BHTOM_API_TOKEN')
    csrf_token = os.getenv('BHTOM_CSRF_TOKEN')
    
    # If not in environment, try to import from config.py
    if not api_token or not csrf_token:
        try:
            from config import BHTOM_API_TOKEN, BHTOM_CSRF_TOKEN, BHTOM_API_BASE_URL
            if not api_base_url:
                api_base_url = BHTOM_API_BASE_URL
            api_token = BHTOM_API_TOKEN
            csrf_token = BHTOM_CSRF_TOKEN
        except ImportError:
            raise ValueError(
                "BHTOM API credentials not found!\n"
                "Please either:\n"
                "1. Set environment variables: BHTOM_API_BASE_URL, BHTOM_API_TOKEN and BHTOM_CSRF_TOKEN\n"
                "2. Create config.py with BHTOM_API_BASE_URL, BHTOM_API_TOKEN and BHTOM_CSRF_TOKEN variables\n"
                "Contact BHTOM administrators to obtain API credentials."
            )
    
    # Default API base URL if not provided
    if not api_base_url:
        api_base_url = "https://bh-tom2.astrolabs.pl/common/api/"
    
    return api_base_url, api_token, csrf_token

# Load credentials and API configuration
try:
    API_BASE_URL, API_TOKEN, CSRF_TOKEN = load_api_config()
    HEADERS = {
        'accept': 'application/json',
        'Authorization': f'Token {API_TOKEN}',
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
    }
except ValueError as e:
    print(f"WARNING: {e}")
    API_BASE_URL = None
    HEADERS = None

def get_data_products(target_name: str, mjd_min: float, mjd_max: float) -> pd.DataFrame:
    """Fetch all data products for a given target and time range.
    
    Args:
        target_name: Name of the target
        mjd_min: Minimum Modified Julian Date
        mjd_max: Maximum Modified Julian Date
        
    Returns:
        DataFrame containing all data products
    """
    dfs = []
    page = 1

    while True:
        request_body = {
            "target_name": target_name,
            "mjd_min": mjd_min,
            "mjd_max": mjd_max,
            "page": page
        }

        response = requests.post(f"{API_BASE_URL}data/", json=request_body, headers=HEADERS)
        if response.status_code != 200:
            break

        data_json = response.json()
        data_list = data_json.get("data", [])
        
        if not data_list:
            break

        df_page = pd.DataFrame(data_list)
        dfs.append(df_page)
        
        print(f"Processed page {page} with {len(df_page)} records")
        
        page += 1
        if page > data_json.get("num_pages", 1):
            break

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def download_photometry_file(data_id: int) -> pd.DataFrame:
    """Download and process a single photometry file.
    
    Args:
        data_id: ID of the data product to download
        
    Returns:
        DataFrame containing the photometry data
    """
    request_body = {"id": data_id}
    response = requests.post(
        f"{API_BASE_URL}downloadPhotometryFile/",
        json=request_body,
        headers=HEADERS
    )
    
    if response.status_code != 200:
        print(f"Failed to download data for ID {data_id}")
        return pd.DataFrame()

    data_io = io.StringIO(response.text)
    return pd.read_csv(
        data_io,
        comment='#',
        sep='\s+',  # Use regex pattern for any whitespace
        header=None,
        names=[
            'NUMBER', 'ALPHA_J2000', 'DELTA_J2000', 'XWIN_IMAGE',
            'YWIN_IMAGE', 'MAG_AUTO', 'MAGERR_AUTO'
        ]
    )

def process_all_data(target_name: str, mjd_min: float, mjd_max: float) -> Dict[str, Dict]:
    """Process all photometry data for a given target and time range.
    
    Args:
        target_name: Name of the target
        mjd_min: Minimum Modified Julian Date
        mjd_max: Maximum Modified Julian Date
        
    Returns:
        Dictionary mapping data IDs to their corresponding data dictionary containing:
        - df: DataFrame with photometry data
        - mjd: Observation date in Modified Julian Date
        - calibration_data: Full calibration data from the API
    """
    # Get all data products
    data_products = get_data_products(target_name, mjd_min, mjd_max)
    if data_products.empty:
        print("No data products found")
        return {}

    # Get all unique IDs and their calibration data
    results = {}
    for _, row in data_products.iterrows():
        data_id = row['id']
        calibration_data = row.get('calibration_data', {})
        mjd = calibration_data.get('mjd') if calibration_data else None
        
        if mjd is None:
            print(f"Warning: No MJD found for data ID: {data_id}")
            continue
            
        print(f"Processing data ID: {data_id} (MJD: {mjd})")
        df = download_photometry_file(data_id)
        
        if not df.empty:
            results[data_id] = {
                'df': df,
                'mjd': mjd,
                'calibration_data': calibration_data
            }

    print(f"Found {len(results)} data products with valid MJD")
    return results

def cross_match_observations(results: Dict[str, Dict], max_separation: float = 1.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Cross-match observations from all files using astropy's coordinate matching.
    
    Args:
        results: Dictionary with photometry results from process_all_data
        max_separation: Maximum separation in arcseconds for matching objects
        
    Returns:
        Tuple containing:
        - measurements_df: DataFrame with MJD and magnitude measurements for each object
        - reference_objects: DataFrame with reference object IDs and their coordinates
    """
    # Sort results by MJD to find the reference epoch
    sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['mjd']))
    
    # Get the reference epoch data (earliest MJD)
    ref_id, ref_data = next(iter(sorted_results.items()))
    ref_df = ref_data['df']
    ref_mjd = ref_data['mjd']
    
    print(f"Using reference epoch MJD {ref_mjd} (ID: {ref_id})")
    
    # Create reference catalog
    reference_objects = pd.DataFrame({
        'REF_ID': range(len(ref_df)),
        'ORIG_NUMBER': ref_df['NUMBER'].values,  # Convert to numpy array
        'RA': ref_df['ALPHA_J2000'].values,      # Convert to numpy array
        'DEC': ref_df['DELTA_J2000'].values      # Convert to numpy array
    })
    
    # Create reference SkyCoord object
    ref_coords = SkyCoord(ra=reference_objects['RA'], dec=reference_objects['DEC'], 
                         unit='deg', frame='icrs')
    
    # Initialize measurements DataFrame
    measurements = []
    
    # Process each epoch
    for data_id, data in sorted_results.items():
        df = data['df']
        mjd = data['mjd']
        
        # Create SkyCoord for current epoch
        current_coords = SkyCoord(ra=df['ALPHA_J2000'].values, 
                                dec=df['DELTA_J2000'].values,
                                unit='deg', frame='icrs')
        
        # Find matches
        idx, d2d, _ = current_coords.match_to_catalog_sky(ref_coords)
        matches = d2d < max_separation*u.arcsec
        
        # Create row for this epoch
        row = {'MJD': mjd}
        
        # Add magnitude and error for each reference object
        for ref_idx in range(len(reference_objects)):
            # Find if there's a match for this reference object
            match_idx = np.where((idx == ref_idx) & matches)[0]
            
            if len(match_idx) > 0:
                # Use the first match if multiple matches exist
                match_data = df.iloc[match_idx[0]]
                row[f'MAG_{ref_idx}'] = match_data['MAG_AUTO']
                row[f'MAGERR_{ref_idx}'] = match_data['MAGERR_AUTO']
            else:
                row[f'MAG_{ref_idx}'] = None
                row[f'MAGERR_{ref_idx}'] = None
        
        measurements.append(row)
    
    # Create measurements DataFrame
    measurements_df = pd.DataFrame(measurements)
    
    print(f"\nMatched {len(reference_objects)} reference objects across {len(measurements)} epochs")
    
    return measurements_df, reference_objects

def main():
    """Main function to download and save photometry data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download photometry data from BHTOM')
    parser.add_argument('target_name', type=str, help='Name of the target')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--days', type=int, help='Number of days to look back')
    group.add_argument('--mjd-range', type=float, nargs=2, metavar=('MJD_MIN', 'MJD_MAX'),
                      help='MJD range (min max)')
    
    args = parser.parse_args()
    
    # Ustawiamy zakres czasowy
    if args.mjd_range:
        mjd_min, mjd_max = args.mjd_range
    else:
        current_mjd = Time.now().mjd
        mjd_min = current_mjd - (args.days or 365)  # default to 365 if days not specified
        mjd_max = current_mjd
    
    print(f"Downloading data for {args.target_name}")
    if args.mjd_range:
        print(f"Time range: MJD {mjd_min:.2f} to {mjd_max:.2f}")
    else:
        print(f"Time range: {args.days or 365} days (MJD {mjd_min:.2f} to {mjd_max:.2f})")

    # Get all photometry data
    results = process_all_data(args.target_name, mjd_min, mjd_max)
    print(f"\nProcessed {len(results)} data products successfully")
    
    # Save raw photometry data
    import pickle
    import os
    os.makedirs('data', exist_ok=True)
    output_file = 'data/photometry_data.pkl'
    with open(output_file, 'wb') as f:
        pickle.dump(results, f)
    print(f"\nRaw photometry data saved to '{output_file}'")
    
    print("\nExample data from first epoch:")
    first_id = next(iter(results))
    first_data = results[first_id]
    print(f"Data ID: {first_id}")
    print(f"MJD: {first_data['mjd']:.6f}")
    print("\nFirst 3 objects:")
    print(first_data['df'].head(3).to_string())
    
if __name__ == "__main__":
    main()
