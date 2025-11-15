import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
import matplotlib.pyplot as plt
import argparse

def read_objects_data(filename: str) -> dict:
    """Read object definitions from objects.dat."""
    objects = {}
    
    # Read CSV file with explicit types
    df = pd.read_csv(filename, header=None, names=['Type', 'RA', 'DEC'])
    
    # Handle target and comparison stars
    for _, row in df.iterrows():
        name = row['Type'].lower()
        ra = float(row['RA'])  # RA in degrees
        dec = float(row['DEC'])  # Dec in degrees
        
        if name == 'target':
            objects['target'] = f"{name},{ra},{dec}"
        else:  # Comparison stars
            objects[name] = {
                'ra': ra,
                'dec': dec
            }
        print(f"Read {name}: RA={ra:.6f}°, Dec={dec:.6f}°")
    
    if 'target' not in objects or 'comp1' not in objects or 'comp2' not in objects:
        raise ValueError("Missing required objects in objects.dat")
    
    return objects

def find_nearest_object(df: pd.DataFrame, ra: float, dec: float, max_distance: float = 5.0) -> tuple:
    """Find the nearest object in DataFrame to given coordinates within max_distance arcseconds."""
    # Filter out invalid coordinates
    valid_coords = df[
        (df['DELTA_J2000'] >= -90) & 
        (df['DELTA_J2000'] <= 90) & 
        (df['ALPHA_J2000'] >= 0) & 
        (df['ALPHA_J2000'] < 360)
    ].copy()
    
    if len(valid_coords) == 0:
        print("Warning: No valid coordinates found in the data")
        return None, None
    
    coords = SkyCoord(ra=valid_coords['ALPHA_J2000'].values*u.degree, 
                     dec=valid_coords['DELTA_J2000'].values*u.degree)
    target = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
    
    # Calculate separations to all objects
    seps = target.separation(coords)
    
    # Find the closest object within max_distance
    min_idx = np.argmin(seps)
    min_sep = seps[min_idx]
    
    if min_sep.arcsec > max_distance:
        return None, None
    
    # Convert index back to original DataFrame index
    original_idx = valid_coords.index[min_idx]
    return original_idx, min_sep.arcsec

def find_nearest_mjd_position(positions_df: pd.DataFrame, mjd: float) -> tuple:
    """Find asteroid position at the nearest MJD."""
    # Find the nearest time
    idx = np.abs(positions_df['MJD'] - mjd).argmin()
    return positions_df.iloc[idx][['RA', 'DEC']]

def process_asteroid_photometry(photometry_data: dict, positions_df: pd.DataFrame, objects: dict) -> pd.DataFrame:
    """Process photometry data using comparison stars."""
    results = []
    
    # Sort positions by MJD
    positions_df = positions_df.sort_values('MJD')
    mjd_min = positions_df['MJD'].min()
    mjd_max = positions_df['MJD'].max()
    
    for data_id, data in photometry_data.items():
        mjd = data['mjd']
        df = data['df']
        
        # Skip if MJD is outside our asteroid position range
        if mjd < mjd_min or mjd > mjd_max:
            print(f"Warning: MJD {mjd} is outside asteroid position range ({mjd_min:.6f} to {mjd_max:.6f})")
            continue
        
        # Find comparison stars
        print(f"\nLooking for stars in data_id {data_id}:")
        print(f"Comp1 target: RA={objects['comp1']['ra']:.6f}°, Dec={objects['comp1']['dec']:.6f}°")
        print(f"Comp2 target: RA={objects['comp2']['ra']:.6f}°, Dec={objects['comp2']['dec']:.6f}°")
        print("First 3 objects in the data:")
        print(df[['ALPHA_J2000', 'DELTA_J2000', 'MAG_AUTO']].head(3))
        
        comp1_idx, comp1_sep = find_nearest_object(df, objects['comp1']['ra'], objects['comp1']['dec'])
        comp2_idx, comp2_sep = find_nearest_object(df, objects['comp2']['ra'], objects['comp2']['dec'])
        
        if comp1_idx is not None:
            print(f"Found Comp1 at separation {comp1_sep:.1f} arcsec")
        if comp2_idx is not None:
            print(f"Found Comp2 at separation {comp2_sep:.1f} arcsec")
        
        if comp1_idx is None or comp2_idx is None:
            print(f"Warning: Could not find comparison stars in data_id {data_id}")
            continue
        
        # Find nearest asteroid position
        ast_pos = find_nearest_mjd_position(positions_df, mjd)
        ast_ra, ast_dec = ast_pos['RA'], ast_pos['DEC']
        
        # Find asteroid with larger search radius (JPL positions can be off by ~15")
        ast_idx, ast_sep = find_nearest_object(df, ast_ra, ast_dec, max_distance=20.0)
        if ast_idx is None:
            print(f"Warning: Could not find asteroid at RA={ast_ra:.6f}°, Dec={ast_dec:.6f}° in data_id {data_id}")
            continue
        
        # Extract magnitudes and check for valid values
        ast_mag = df.iloc[ast_idx]['MAG_AUTO']
        ast_magerr = df.iloc[ast_idx]['MAGERR_AUTO']
        comp1_mag = df.iloc[comp1_idx]['MAG_AUTO']
        comp2_mag = df.iloc[comp2_idx]['MAG_AUTO']
        
        # Skip if any magnitude is invalid
        if not all(np.isfinite([ast_mag, ast_magerr, comp1_mag, comp2_mag])):
            print(f"Warning: Invalid magnitude values in data_id {data_id}")
            continue
        
        result = {
            'MJD': mjd,
            'AST_RA': ast_ra,
            'AST_DEC': ast_dec,
            'AST_SEP': ast_sep,
            'AST_MAG': ast_mag,
            'AST_MAGERR': ast_magerr,
            'COMP1_MAG': comp1_mag,
            'COMP2_MAG': comp2_mag
        }
        results.append(result)
    
    return pd.DataFrame(results)

def process_static_object_photometry(photometry_data: dict, target_coords: dict, comp_stars: dict) -> pd.DataFrame:
    """Process photometry data for a static object using comparison stars.
    
    Args:
        photometry_data (dict): Dictionary containing photometry data for each epoch
        target_coords (dict): Dictionary with target object coordinates {'ra': float, 'dec': float}
        comp_stars (dict): Dictionary with comparison stars coordinates {'comp1': {'ra': float, 'dec': float}, 'comp2': {...}}
    
    Returns:
        pd.DataFrame: Processed photometry results
    """
    results = []
    
    for data_id, data in photometry_data.items():
        mjd = data['mjd']
        df = data['df']
        
        # Find target and comparison stars
        print(f"\nLooking for stars in data_id {data_id}:")
        target_idx, target_sep = find_nearest_object(df, target_coords['ra'], target_coords['dec'])
        comp1_idx, comp1_sep = find_nearest_object(df, comp_stars['comp1']['ra'], comp_stars['comp1']['dec'])
        comp2_idx, comp2_sep = find_nearest_object(df, comp_stars['comp2']['ra'], comp_stars['comp2']['dec'])
        
        # Check if all objects were found
        if any(idx is None for idx in [target_idx, comp1_idx, comp2_idx]):
            print(f"Warning: Could not find all objects in data_id {data_id}")
            continue
            
        # Extract magnitudes and check for valid values
        target_mag = df.iloc[target_idx]['MAG_AUTO']
        target_magerr = df.iloc[target_idx]['MAGERR_AUTO']
        comp1_mag = df.iloc[comp1_idx]['MAG_AUTO']
        comp2_mag = df.iloc[comp2_idx]['MAG_AUTO']
        
        # Skip if any magnitude is invalid
        if not all(np.isfinite([target_mag, target_magerr, comp1_mag, comp2_mag])):
            print(f"Warning: Invalid magnitude values in data_id {data_id}")
            continue
        
        result = {
            'MJD': mjd,
            'TARGET_RA': df.iloc[target_idx]['ALPHA_J2000'],
            'TARGET_DEC': df.iloc[target_idx]['DELTA_J2000'],
            'TARGET_SEP': target_sep,
            'TARGET_MAG': target_mag,
            'TARGET_MAGERR': target_magerr,
            'COMP1_MAG': comp1_mag,
            'COMP2_MAG': comp2_mag
        }
        results.append(result)
    
    return pd.DataFrame(results)

def plot_magnitude_ratios(results: pd.DataFrame, save_path: str = 'magnitude_ratios.png', 
                          ylim_sigma_factor: float = 3.0):
    """Plot magnitude ratios between target and comparison stars.
    Optimized for shallow exoplanet transit detection.
    
    Args:
        results: DataFrame with photometry results
        save_path: Path to save the plot
        ylim_sigma_factor: Y-axis limit factor (median ± factor * std), default: 3.0
    """
    # Calculate magnitude differences
    results['TARGET_COMP1'] = results['TARGET_MAG'] - results['COMP1_MAG']
    results['TARGET_COMP2'] = results['TARGET_MAG'] - results['COMP2_MAG']
    results['COMP1_COMP2'] = results['COMP1_MAG'] - results['COMP2_MAG']
    
    # Calculate relative time in hours from first observation
    time_offset = results['MJD'].min()
    results['TIME_HOURS'] = (results['MJD'] - time_offset) * 24

    # Create figure with 3 subplots
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f'Differential Photometry\nMJD {time_offset:.5f} + hours', 
                 fontsize=14, fontweight='bold')

    # Plot 1: Target - Comp1 (main light curve)
    ax1 = axes[0]
    ax1.errorbar(results['TIME_HOURS'], results['TARGET_COMP1'], 
                yerr=results['TARGET_MAGERR'], 
                fmt='o', markersize=4, color='blue', capsize=2, alpha=0.7)
    median1 = results['TARGET_COMP1'].median()
    std1 = results['TARGET_COMP1'].std()
    ax1.axhline(median1, color='red', linestyle='--', alpha=0.5, label=f'Median: {median1:.4f}')
    ylim_range1 = ylim_sigma_factor * std1
    ax1.set_ylim(median1 + ylim_range1, median1 - ylim_range1)  # Inverted, ±(factor*σ) mag range
    ax1.set_ylabel('Target - Comp1 [mag]', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    stats1 = f"σ = {std1:.4f} mag"
    ax1.text(0.02, 0.95, stats1, transform=ax1.transAxes, 
             bbox=dict(facecolor='white', alpha=0.8), va='top', fontsize=10)

    # Plot 2: Target - Comp2 (verification light curve)
    ax2 = axes[1]
    ax2.errorbar(results['TIME_HOURS'], results['TARGET_COMP2'], 
                yerr=results['TARGET_MAGERR'], 
                fmt='o', markersize=4, color='red', capsize=2, alpha=0.7)
    median2 = results['TARGET_COMP2'].median()
    std2 = results['TARGET_COMP2'].std()
    ax2.axhline(median2, color='blue', linestyle='--', alpha=0.5, label=f'Median: {median2:.4f}')
    ylim_range2 = ylim_sigma_factor * std2
    ax2.set_ylim(median2 + ylim_range2, median2 - ylim_range2)  # Inverted, ±(factor*σ) mag range
    ax2.set_ylabel('Target - Comp2 [mag]', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    stats2 = f"σ = {std2:.4f} mag"
    ax2.text(0.02, 0.95, stats2, transform=ax2.transAxes, 
             bbox=dict(facecolor='white', alpha=0.8), va='top', fontsize=10)

    # Plot 3: Comp1 - Comp2 (check star stability)
    ax3 = axes[2]
    comp_err = np.sqrt(2) * results['TARGET_MAGERR'].median()  # Approximate error
    ax3.errorbar(results['TIME_HOURS'], results['COMP1_COMP2'], 
                yerr=comp_err,
                fmt='o', markersize=4, color='green', capsize=2, alpha=0.7)
    median3 = results['COMP1_COMP2'].median()
    std3 = results['COMP1_COMP2'].std()
    ax3.axhline(median3, color='purple', linestyle='--', alpha=0.5, label=f'Median: {median3:.4f}')
    ylim_range3 = ylim_sigma_factor * std3
    ax3.set_ylim(median3 + ylim_range3, median3 - ylim_range3)  # Inverted, ±(factor*σ) mag range
    ax3.set_ylabel('Comp1 - Comp2 [mag]', fontsize=11)
    ax3.set_xlabel('Time [hours from first observation]', fontsize=11)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right')
    stats3 = f"σ = {std3:.4f} mag (check stability)"
    ax3.text(0.02, 0.95, stats3, transform=ax3.transAxes, 
             bbox=dict(facecolor='white', alpha=0.8), va='top', fontsize=10)

    # Save plot
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"\nPlot saved to {save_path}")

def filter_photometry_data(photometry_data: dict, filter_name: str = None) -> dict:
    """Filter photometry data by band/filter.
    
    Args:
        photometry_data: Dictionary with photometry data
        filter_name: Filter name (e.g., 'R', 'V', 'I', 'g', 'r', 'i'). If None, return all data.
        
    Returns:
        Filtered dictionary with photometry data
    """
    if filter_name is None:
        return photometry_data
    
    filtered_data = {}
    for data_id, data_dict in photometry_data.items():
        calibration_data = data_dict.get('calibration_data', {})
        band = calibration_data.get('band', '').upper()
        
        if band == filter_name.upper():
            filtered_data[data_id] = data_dict
    
    return filtered_data

def main():
    """Main function to process photometry data."""
    import os
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Process differential photometry from BHTOM data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python process_photometry.py              # Process all filters
  python process_photometry.py --filter R   # Process only R-band data
  python process_photometry.py --filter V   # Process only V-band data
  python process_photometry.py -f g         # Process only g-band data
        '''
    )
    parser.add_argument(
        '--filter', '-f',
        type=str,
        default=None,
        help='Filter/band name to process (e.g., R, V, I, g, r, i). If not specified, all filters are processed.'
    )
    parser.add_argument(
        '--ylim-sigma',
        type=float,
        default=3.0,
        help='Y-axis limit factor: median ± (factor * std). Default: 3.0'
    )
    
    args = parser.parse_args()
    
    # Configuration parameters
    YLIM_SIGMA_FACTOR = args.ylim_sigma  # Y-axis limit factor: median ± (factor * std)
    
    # Create output directories
    os.makedirs('output', exist_ok=True)
    os.makedirs('plots', exist_ok=True)
    
    # Read object definitions
    objects = read_objects_data('objects.dat')
    print("Read object definitions:")
    print(f"Target: {objects['target']}")
    print(f"Comp1: RA={objects['comp1']['ra']:.6f}°, Dec={objects['comp1']['dec']:.6f}°")
    print(f"Comp2: RA={objects['comp2']['ra']:.6f}°, Dec={objects['comp2']['dec']:.6f}°")
    print()
    
    # Read photometry data
    data_file = 'data/photometry_data.pkl'
    if not os.path.exists(data_file):
        data_file = 'photometry_data.pkl'  # Fallback to old location
    
    with open(data_file, 'rb') as f:
        import pickle
        photometry_data = pickle.load(f)
    print(f"Read photometry data for {len(photometry_data)} epochs (all filters)")
    
    # Filter by band if specified
    if args.filter:
        print(f"\nFiltering data for filter: {args.filter}")
        photometry_data = filter_photometry_data(photometry_data, args.filter)
        print(f"After filtering: {len(photometry_data)} epochs in {args.filter} band")
        
        if len(photometry_data) == 0:
            print(f"\nERROR: No data found for filter '{args.filter}'")
            print("\nAvailable filters in the data:")
            with open(data_file, 'rb') as f:
                all_data = pickle.load(f)
            filters = set()
            for data_dict in all_data.values():
                band = data_dict.get('calibration_data', {}).get('band', 'Unknown')
                filters.add(band)
            print(f"  {', '.join(sorted(filters))}")
            return
    else:
        print("\nProcessing all filters (no filter specified)")
    
    # Prepare coordinates for static object photometry
    target_coords = {'ra': float(objects['target'].split(',')[1]), 'dec': float(objects['target'].split(',')[2])}
    comp_stars = {
        'comp1': {'ra': objects['comp1']['ra'], 'dec': objects['comp1']['dec']},
        'comp2': {'ra': objects['comp2']['ra'], 'dec': objects['comp2']['dec']}
    }
    
    # Process photometry
    results = process_static_object_photometry(photometry_data, target_coords, comp_stars)
    
    # Save results
    output_file = 'output/photometry_results.csv'
    results.to_csv(output_file, index=False)
    print(f"Results saved to '{output_file}'")
    
    if len(results) == 0:
        print("\nNo valid measurements found!")
        return
        
    print(f"\nProcessed {len(results)} measurements")
    
    # Plot magnitude ratios
    plot_magnitude_ratios(results, save_path='plots/magnitude_ratios.png', 
                         ylim_sigma_factor=YLIM_SIGMA_FACTOR)
    
    print("\nExample results (first 3 measurements):")
    example = results.head(3)
    if len(example) > 0:
        print("\nTime and position:")
        pos_cols = ['MJD', 'TARGET_RA', 'TARGET_DEC', 'TARGET_SEP']
        pos = example[pos_cols].copy()
        for col in ['TARGET_RA', 'TARGET_DEC']:
            pos[col] = pos[col].map(lambda x: f"{x:10.6f}")
        pos['TARGET_SEP'] = pos['TARGET_SEP'].map(lambda x: f"{x:6.3f}")
        print(pos.to_string())
        
        print("\nMagnitudes:")
        mag_cols = ['MJD', 'TARGET_MAG', 'TARGET_MAGERR', 'COMP1_MAG', 'COMP2_MAG']
        mags = example[mag_cols].copy()
        for col in mag_cols[1:]:
            mags[col] = mags[col].map(lambda x: f"{x:7.4f}")
        print(mags.to_string())

if __name__ == "__main__":
    main()
