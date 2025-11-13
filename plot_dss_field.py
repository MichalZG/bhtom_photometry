import requests
from io import BytesIO
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np

def read_objects_data(filename='objects.dat'):
    """Read object coordinates from file."""
    print(f"Reading coordinates from {filename}")
    objects = {}
    with open(filename, 'r') as f:
        for line in f:
            obj_type, ra, dec = line.strip().split(',')
            objects[obj_type] = {
                'ra': float(ra),
                'dec': float(dec)
            }
            print(f"Found {obj_type}: RA={ra}°, Dec={dec}°")
    return objects

def plot_dss_field():
    print("\n=== Starting DSS field plot generation ===")
    # Read object coordinates
    objects = read_objects_data()
    
    # Get target coordinates
    target_ra = objects['Target']['ra']
    target_dec = objects['Target']['dec']
    print(f"\nTarget coordinates: RA={target_ra}°, Dec={target_dec}°")
    
    # Create SkyCoord object for the target
    target_coord = SkyCoord(ra=target_ra*u.deg, dec=target_dec*u.deg)
    print(f"Target coordinates in HMS/DMS: {target_coord.to_string('hmsdms')}")
    
    # Get DSS image
    print("\nDownloading DSS image...")
    print(f"Position: {target_coord.to_string('decimal')}")
    print("Image size: 15 arcmin")
    
    # Format coordinates for ESO DSS URL
    ra_deg = f"{target_ra:.6f}"
    dec_deg = f"{target_dec:+.6f}"
    url = f'http://archive.eso.org/dss/dss/image?ra={ra_deg}&dec={dec_deg}&equinox=J2000&name=&x=15&y=15&Sky-Survey=DSS2-red&mime-type=download-fits'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            image = fits.open(image_data, ignore_missing_simple=True)
            print("Image downloaded successfully")
        else:
            raise Exception(f"Failed to download image: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        raise
    
    # Create figure
    plt.figure(figsize=(10, 10))
    
    # Plot DSS image
    print("\nProcessing image...")
    img = image[0].data
    # Normalize image data for better display
    img = np.clip(img, np.percentile(img, 1), np.percentile(img, 99))
    print(f"Image shape: {img.shape}")
    plt.imshow(img, cmap='gray_r', origin='lower')
    plt.gca().set_axis_off()
    
    # Get image WCS
    print("Setting up WCS coordinates...")
    wcs = WCS(image[0].header)
    print(f"WCS info: {wcs}")
    
    # Plot objects
    print("\nPlotting objects...")
    colors = {'Target': 'red', 'Comp1': 'blue', 'Comp2': 'green'}
    markers = {'Target': 'o', 'Comp1': 's', 'Comp2': 'D'}
    sizes = {'Target': 100, 'Comp1': 80, 'Comp2': 80}
    
    for obj_type, coords in objects.items():
        print(f"\nProcessing {obj_type}...")
        # Convert sky coordinates to pixel coordinates
        x, y = wcs.wcs_world2pix(coords['ra'], coords['dec'], 0)
        print(f"Sky coordinates: RA={coords['ra']:.3f}°, Dec={coords['dec']:.3f}°")
        print(f"Pixel coordinates: x={x:.1f}, y={y:.1f}")
        
        # Plot marker
        plt.plot(x, y, markers[obj_type], color=colors[obj_type], 
                ms=10, label=obj_type, mfc='none', mew=2)
        
        # Add label with coordinates
        plt.annotate(f"{obj_type}\nRA: {coords['ra']:.3f}°\nDec: {coords['dec']:.3f}°",
                    (x, y), xytext=(10, 10), textcoords='offset points',
                    bbox=dict(facecolor='white', alpha=0.7),
                    color=colors[obj_type])
    
    plt.title(f"DSS2 Red image of HWvir field\n{target_ra:.3f}°, {target_dec:.3f}°")
    plt.colorbar(label='Flux')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Save plot
    print("\nSaving plot...")
    plt.tight_layout()
    import os
    os.makedirs('plots', exist_ok=True)
    output_file = 'plots/dss_field.png'
    plt.savefig(output_file, dpi=150)
    print(f"Plot saved as {output_file} with DPI=150")
    print("\n=== DSS field plot generation completed ===")

if __name__ == '__main__':
    plot_dss_field()
