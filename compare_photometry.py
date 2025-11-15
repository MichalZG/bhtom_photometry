import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Read data
results_file = 'output/photometry_results.csv' if os.path.exists('output/photometry_results.csv') else 'photometry_results.csv'
results = pd.read_csv(results_file)
other = pd.read_csv('wasp-46b_datasubset.dat', delimiter='\t')

# Sort both datasets by time
results = results.sort_values('MJD').reset_index(drop=True)
other = other.sort_values('#JD_UTC').reset_index(drop=True)

# Convert JD to MJD in the other dataset
other['MJD'] = other['#JD_UTC'] - 2400000.5

# Calculate time offset (first integer MJD)
time_offset = int(min(results['MJD'].min(), other['MJD'].min()))

# Print first points from both datasets and their time difference
print("\nFirst points times:")
print(f"BHT first point MJD:   {results['MJD'].iloc[0]}")
print(f"AIJ first point MJD: {other['MJD'].iloc[0]}")
time_diff_first = abs(results['MJD'].iloc[0] - other['MJD'].iloc[0]) * 24 * 3600
print(f"Time difference: {time_diff_first:.3f} seconds")

# Find pairs of points that are close in time (within 180 seconds / 3 minutes)
TIME_THRESHOLD = 180.0 / (24 * 3600)  # 180 seconds converted to days

# Create empty lists to store matching pairs
matching_pairs = []

# For each point in our results, find the closest point in other dataset
for _, our_row in results.iterrows():
    time_diff = abs(other['MJD'] - our_row['MJD'])
    min_diff_idx = time_diff.argmin()
    min_diff = time_diff[min_diff_idx]
    
    # If the closest point is within threshold, save this pair
    if min_diff <= TIME_THRESHOLD:
        matching_pairs.append({
            'MJD_our': our_row['MJD'],
            'TARGET_MAG': our_row['TARGET_MAG'],
            'TARGET_MAGERR': our_row['TARGET_MAGERR'],
            'COMP1_MAG': our_row['COMP1_MAG'],
            'COMP2_MAG': our_row['COMP2_MAG'],
            'MJD_other': other['MJD'].iloc[min_diff_idx],
            'rel_flux_T1': other['rel_flux_T1'].iloc[min_diff_idx],
            'rel_flux_C2': other['rel_flux_C2'].iloc[min_diff_idx],
            'rel_flux_C3': other['rel_flux_C3'].iloc[min_diff_idx]
        })

# Convert list of pairs to DataFrame
merged = pd.DataFrame(matching_pairs)

if len(merged) == 0:
    print("\nWARNING: No matching time points found within threshold!")
    print(f"Time threshold: {TIME_THRESHOLD * 24 * 3600:.1f} seconds")
    exit(1)

# Calculate time differences
time_diff = abs(merged['MJD_our'] - merged['MJD_other']) * 24 * 3600  # Convert to seconds
print(f"\nFound {len(merged)} matching time points")
print(f"Time differences statistics (seconds):")
print(f"  Mean: {time_diff.mean():.3f}")
print(f"  Max:  {time_diff.max():.3f}")
print(f"  Min:  {time_diff.min():.3f}")
print(f"  Std:  {time_diff.std():.3f}")

# Calculate magnitude differences for BHT dataset
bht_target_comp1 = merged['TARGET_MAG'] - merged['COMP1_MAG']
bht_target_comp2 = merged['TARGET_MAG'] - merged['COMP2_MAG']
bht_comp1_comp2 = merged['COMP1_MAG'] - merged['COMP2_MAG']

# Calculate magnitude differences for AIJ dataset
aij_target_comp1 = -2.5 * np.log10(merged['rel_flux_T1'] / merged['rel_flux_C2'])
aij_target_comp2 = -2.5 * np.log10(merged['rel_flux_T1'] / merged['rel_flux_C3'])
aij_comp1_comp2 = -2.5 * np.log10(merged['rel_flux_C2'] / merged['rel_flux_C3'])

# Convert time to hours from first observation
time_hours_bht = (merged['MJD_our'] - time_offset) * 24
time_hours_aij = (merged['MJD_other'] - time_offset) * 24

# Create figure with 5 subplots (2 for light curves, 3 for residuals)
fig, axs = plt.subplots(5, 1, figsize=(14, 16), height_ratios=[1.5, 1.5, 1, 1, 1])
fig.suptitle(f'Photometry Comparison: PSF (BHTOM) vs Aperture (AIJ)\nMJD {time_offset:.5f} + hours', 
             fontsize=14, fontweight='bold')
plt.subplots_adjust(hspace=0.3)

# Plot 1: BHT light curves
ax_bht = axs[0]
ax_bht.errorbar(time_hours_bht, bht_target_comp1, 
               yerr=merged['TARGET_MAGERR'],
               fmt='o', markersize=4, label='Target-Comp1', color='blue', capsize=2, alpha=0.7)
ax_bht.plot(time_hours_bht, bht_target_comp2,
          'o', markersize=4, label='Target-Comp2', color='red', alpha=0.7)
ax_bht.plot(time_hours_bht, bht_comp1_comp2,
          'o', markersize=3, label='Comp1-Comp2', color='green', alpha=0.5)

# Set optimized y-axis limits for BHT (±0.1 mag from median of target-comp1)
median_bht = np.median(bht_target_comp1)
ax_bht.set_ylim(median_bht + 0.1, median_bht - 0.1)  # Inverted
ax_bht.set_ylabel('Differential Mag [mag]', fontsize=11)
ax_bht.set_title('PSF Photometry (BHTOM)', fontsize=12, fontweight='bold')
ax_bht.grid(True, alpha=0.3)
ax_bht.legend(loc='upper right')
ax_bht.axhline(median_bht, color='gray', linestyle='--', alpha=0.3)

# Plot 2: AIJ light curves
ax_aij = axs[1]
ax_aij.plot(time_hours_aij, aij_target_comp1,
          's', markersize=4, label='Target-Comp2', color='blue', alpha=0.7)
ax_aij.plot(time_hours_aij, aij_target_comp2,
          's', markersize=4, label='Target-Comp3', color='red', alpha=0.7)
ax_aij.plot(time_hours_aij, aij_comp1_comp2,
          's', markersize=3, label='Comp2-Comp3', color='green', alpha=0.5)

# Set optimized y-axis limits for AIJ (±0.1 mag from median of target-comp1)
median_aij = np.median(aij_target_comp1)
ax_aij.set_ylim(median_aij + 0.1, median_aij - 0.1)  # Inverted
ax_aij.set_ylabel('Differential Mag [mag]', fontsize=11)
ax_aij.set_title('Aperture Photometry (AIJ)', fontsize=12, fontweight='bold')
ax_aij.grid(True, alpha=0.3)
ax_aij.legend(loc='upper right')
ax_aij.axhline(median_aij, color='gray', linestyle='--', alpha=0.3)

# Calculate residuals directly for matching points (AIJ - BHT)
res_target_comp1 = aij_target_comp1 - bht_target_comp1
res_target_comp2 = aij_target_comp2 - bht_target_comp2
res_comp1_comp2 = aij_comp1_comp2 - bht_comp1_comp2

# Plot 3: Target-Comp1 residuals
ax_res1 = axs[2]
ax_res1.plot(time_hours_bht, res_target_comp1, 
            'o', markersize=3, color='blue', alpha=0.7)
ax_res1.axhline(y=0, color='k', linestyle='--', alpha=0.5)

# Calculate statistics for Target-Comp1
median1 = np.median(res_target_comp1)
std1 = np.std(res_target_comp1)
mean1 = np.mean(res_target_comp1)
ax_res1.axhline(y=median1, color='red', linestyle=':', alpha=0.5, label=f'Median: {median1:.3f}')

# Set y-axis limits: ±0.05 mag from median
ax_res1.set_ylim(median1 - 0.05, median1 + 0.05)

ax_res1.set_ylabel('Residuals [mag]', fontsize=10)
ax_res1.set_title(f'Target-Comp Residuals (Aperture - PSF)  |  σ={std1:.4f} mag', fontsize=11)
ax_res1.grid(True, alpha=0.3)
ax_res1.legend(loc='upper right', fontsize=9)

# Add statistics text for Target-Comp1
stats_text = (f'Mean: {mean1:.3f} mag\n'
             f'Median: {median1:.3f} mag\n'
             f'Std: {std1:.3f} mag\n'
             f'Range: [{median1-std1:.3f}, {median1+std1:.3f}] mag')
ax_res1.text(0.02, 0.98, stats_text,
             transform=ax_res1.transAxes,
             verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.8))

# Plot 4: Target-Comp2 residuals (verification)
ax_res2 = axs[3]
ax_res2.plot(time_hours_bht, res_target_comp2, 
            'o', markersize=3, color='red', alpha=0.7)
ax_res2.axhline(y=0, color='k', linestyle='--', alpha=0.5)

# Calculate statistics for Target-Comp2
median2 = np.median(res_target_comp2)
std2 = np.std(res_target_comp2)
mean2 = np.mean(res_target_comp2)
ax_res2.axhline(y=median2, color='blue', linestyle=':', alpha=0.5, label=f'Median: {median2:.3f}')

# Set y-axis limits: ±0.05 mag from median
ax_res2.set_ylim(median2 - 0.05, median2 + 0.05)

ax_res2.set_ylabel('Residuals [mag]', fontsize=10)
ax_res2.set_title(f'Target-Comp2 Residuals (Aperture - PSF)  |  σ={std2:.4f} mag', fontsize=11)
ax_res2.grid(True, alpha=0.3)
ax_res2.legend(loc='upper right', fontsize=9)

# Add statistics text for Target-Comp2
stats_text = (f'Mean: {mean2:.3f} mag\n'
             f'Median: {median2:.3f} mag\n'
             f'Std: {std2:.3f} mag\n'
             f'Range: [{median2-std2:.3f}, {median2+std2:.3f}] mag')
ax_res2.text(0.02, 0.98, stats_text,
             transform=ax_res2.transAxes,
             verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.8))

# Plot 5: Comp-Comp residuals (check stability)
ax_res3 = axs[4]
ax_res3.plot(time_hours_bht, res_comp1_comp2, 
            'o', markersize=3, color='green', alpha=0.7)
ax_res3.axhline(y=0, color='k', linestyle='--', alpha=0.5)

# Calculate statistics for Comp1-Comp2
median3 = np.median(res_comp1_comp2)
std3 = np.std(res_comp1_comp2)
mean3 = np.mean(res_comp1_comp2)
ax_res3.axhline(y=median3, color='purple', linestyle=':', alpha=0.5, label=f'Median: {median3:.3f}')

# Set y-axis limits: ±0.05 mag from median
ax_res3.set_ylim(median3 - 0.05, median3 + 0.05)

ax_res3.set_xlabel('Time [hours from first observation]', fontsize=11)
ax_res3.set_ylabel('Residuals [mag]', fontsize=10)
ax_res3.set_title(f'Comp-Comp Residuals (Aperture - PSF)  |  σ={std3:.4f} mag (stability check)', fontsize=11)
ax_res3.grid(True, alpha=0.3)
ax_res3.legend(loc='upper right', fontsize=9)

# Add statistics text for Comp1-Comp2
stats_text = (f'Mean: {mean3:.3f} mag\n'
             f'Median: {median3:.3f} mag\n'
             f'Std: {std3:.3f} mag\n'
             f'Range: [{median3-std3:.3f}, {median3+std3:.3f}] mag')
ax_res3.text(0.02, 0.98, stats_text,
             transform=ax_res3.transAxes,
             verticalalignment='top',
             bbox=dict(facecolor='white', alpha=0.8))

# Print statistics
print("\nResiduals statistics (AIJ - BHT):")
print(f"Target-Comp1: mean = {np.mean(res_target_comp1):.3f} ± {np.std(res_target_comp1):.3f}")
print(f"Target-Comp2: mean = {np.mean(res_target_comp2):.3f} ± {np.std(res_target_comp2):.3f}")
print(f"Comp1-Comp2: mean = {np.mean(res_comp1_comp2):.3f} ± {np.std(res_comp1_comp2):.3f}")

# Create plots directory if needed
os.makedirs('plots', exist_ok=True)
output_plot = 'plots/photometry_comparison.png'
plt.savefig(output_plot)
print(f"\nPlot saved to {output_plot}")
