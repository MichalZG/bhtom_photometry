#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert photometry_results.csv from magnitude format to flux format.
Output: JD_UTC, flux_source, error_flux_source
"""

import pandas as pd
import numpy as np

def mag_to_flux(mag, mag_err=None, reference_flux=1.0):
    """
    Convert magnitude to flux.
    
    Args:
        mag: Magnitude value
        mag_err: Magnitude error (optional)
        reference_flux: Reference flux at magnitude 0 (default: 1.0)
    
    Returns:
        flux: Flux value
        flux_err: Flux error (if mag_err provided)
    """
    # Flux = reference_flux * 10^(-mag/2.5)
    flux = reference_flux * 10**(-mag / 2.5)
    
    if mag_err is not None:
        # Error propagation: dF/F = (ln(10)/2.5) * dmag
        # flux_err = flux * (ln(10)/2.5) * mag_err
        flux_err = flux * (np.log(10) / 2.5) * mag_err
        return flux, flux_err
    
    return flux

def convert_photometry_to_flux(input_file=None, 
                                 output_file='output/photometry_results_flux.csv'):
    """
    Convert photometry results from magnitude to flux format.
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
    
    # Convert target magnitude to flux
    print("\nConverting magnitudes to fluxes...")
    target_flux, target_flux_err = mag_to_flux(df['TARGET_MAG'].values, 
                                                 df['TARGET_MAGERR'].values)
    
    # Also convert comparison stars for reference
    comp1_flux = mag_to_flux(df['COMP1_MAG'].values)
    comp2_flux = mag_to_flux(df['COMP2_MAG'].values)
    
    # Create output dataframe
    output_df = pd.DataFrame({
        'JD_UTC': df['JD_UTC'],
        'flux_source': target_flux,
        'error_flux_source': target_flux_err,
        'flux_comp1': comp1_flux,
        'flux_comp2': comp2_flux,
        # Keep additional columns for reference
        'TARGET_RA': df['TARGET_RA'],
        'TARGET_DEC': df['TARGET_DEC'],
        'TARGET_SEP': df['TARGET_SEP']
    })
    
    # Save to file
    output_df.to_csv(output_file, index=False, float_format='%.8f')
    print(f"\nFlux photometry saved to {output_file}")
    
    # Display statistics
    print("\nFlux statistics:")
    print(f"Target flux: mean = {target_flux.mean():.6f}, std = {target_flux.std():.6f}")
    print(f"Target flux error: mean = {target_flux_err.mean():.6f}, median = {np.median(target_flux_err):.6f}")
    
    # Display first few rows
    print("\nFirst 5 measurements:")
    print(output_df[['JD_UTC', 'flux_source', 'error_flux_source']].head().to_string())
    
    # Also create a simplified version with only JD_UTC, flux, error
    simple_df = output_df[['JD_UTC', 'flux_source', 'error_flux_source']].copy()
    simple_output = output_file.replace('.csv', '_simple.dat')
    
    # Save as space-separated file with # in header
    with open(simple_output, 'w') as f:
        # Write header with # prefix
        f.write('#JD_UTC\tflux_source\terror_flux_source\n')
        # Write data rows
        for _, row in simple_df.iterrows():
            f.write(f"{row['JD_UTC']:.10f}\t{row['flux_source']:.10e}\t{row['error_flux_source']:.10e}\n")
    
    print(f"\nSimplified flux file (JD_UTC, flux_source, error_flux_source only) saved to {simple_output}")
    print(f"Format: space/tab separated with # header")
    
    return output_df

if __name__ == '__main__':
    convert_photometry_to_flux()
