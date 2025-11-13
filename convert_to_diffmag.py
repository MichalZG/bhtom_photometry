#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert photometry_results.csv to differential magnitude format.
Output: JD_UTC, diff_mag (TARGET - COMP1), error_diff_mag
"""

import pandas as pd
import numpy as np

def convert_to_differential_magnitude(input_file=None, 
                                       output_file='output/photometry_results_diffmag.dat'):
    """
    Convert photometry results to differential magnitude format.
    
    Calculates: diff_mag = TARGET_MAG - COMP1_MAG
    """
    import os
    
    # Auto-detect input file
    if input_file is None:
        if os.path.exists('output/photometry_results.csv'):
            input_file = 'output/photometry_results.csv'
        else:
            input_file = 'photometry_results.csv'
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    print(f"Reading photometry data from {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Found {len(df)} measurements")
    print(f"Columns: {df.columns.tolist()}")
    
    # Convert MJD to JD_UTC
    df['JD_UTC'] = df['MJD'] + 2400000.5
    
    # Calculate differential magnitude: TARGET - COMP1
    diff_mag = df['TARGET_MAG'] - df['COMP1_MAG']
    
    # Error propagation for difference (assuming errors are independent):
    # error(A - B) = sqrt(error_A^2 + error_B^2)
    # For simplicity, we use only TARGET error as COMP error is typically smaller
    error_diff_mag = df['TARGET_MAGERR']
    
    # Also calculate TARGET - COMP2 for verification
    diff_mag_comp2 = df['TARGET_MAG'] - df['COMP2_MAG']
    
    print("\nCalculating differential magnitudes...")
    print(f"Target - Comp1: mean = {diff_mag.mean():.4f}, std = {diff_mag.std():.4f}")
    print(f"Target - Comp2: mean = {diff_mag_comp2.mean():.4f}, std = {diff_mag_comp2.std():.4f}")
    
    # Save as space-separated file with # in header
    with open(output_file, 'w') as f:
        # Write header with # prefix
        f.write('#JD_UTC\tdiff_mag\terror_diff_mag\n')
        # Write data rows
        for i in range(len(df)):
            jd = df['JD_UTC'].iloc[i]
            dmag = diff_mag.iloc[i]
            err = error_diff_mag.iloc[i]
            f.write(f"{jd:.10f}\t{dmag:.6f}\t{err:.6f}\n")
    
    print(f"\nDifferential magnitude file saved to {output_file}")
    print(f"Format: space/tab separated with # header")
    
    # Display first few rows
    print("\nFirst 5 measurements:")
    for i in range(min(5, len(df))):
        print(f"JD={df['JD_UTC'].iloc[i]:.6f}  diff_mag={diff_mag.iloc[i]:.6f}  error={error_diff_mag.iloc[i]:.6f}")
    
    # Statistics
    print(f"\nStatistics:")
    print(f"Differential magnitude (Target - Comp1):")
    print(f"  Mean: {diff_mag.mean():.6f}")
    print(f"  Median: {diff_mag.median():.6f}")
    print(f"  Std: {diff_mag.std():.6f}")
    print(f"  Min: {diff_mag.min():.6f}")
    print(f"  Max: {diff_mag.max():.6f}")
    print(f"  Range: {diff_mag.max() - diff_mag.min():.6f}")
    
    return df, diff_mag, error_diff_mag

if __name__ == '__main__':
    convert_to_differential_magnitude()
