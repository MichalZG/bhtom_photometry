#!/usr/bin/env python3
"""
BHTOM Photometry Web Interface
A Flask web application for processing photometric data from BHTOM.
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import subprocess
import json
import glob
from datetime import datetime
import threading
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Store job status
jobs = {}

def run_pipeline(job_id, target_name, mjd_min, mjd_max, filter_name, objects_data):
    """Run the photometry pipeline in a background thread."""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['step'] = 'Saving object coordinates'
        
        # Save objects.dat
        with open('objects.dat', 'w') as f:
            f.write(objects_data)
        
        # Step 1: Download data
        jobs[job_id]['step'] = 'Downloading data from BHTOM'
        result = subprocess.run(
            ['./venv/bin/python', 'get_data_bhtom.py', target_name, 
             '--mjd-range', str(mjd_min), str(mjd_max)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f"Download failed: {result.stderr}"
            return
        
        # Parse number of epochs from output
        for line in result.stdout.split('\n'):
            if 'data products with valid MJD' in line:
                jobs[job_id]['epochs_downloaded'] = line.split()[1]
        
        # Step 2: Process photometry
        jobs[job_id]['step'] = 'Processing photometry'
        cmd = ['./venv/bin/python', 'process_photometry.py']
        if filter_name and filter_name != 'all':
            cmd.extend(['--filter', filter_name])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = f"Processing failed: {result.stderr}"
            return
        
        # Step 3: Generate DSS field plot
        jobs[job_id]['step'] = 'Generating DSS field plot'
        result = subprocess.run(
            ['./venv/bin/python', 'plot_dss_field.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Find generated files
        jobs[job_id]['files'] = {
            'results': 'output/photometry_results.csv',
            'plot_lightcurve': 'plots/magnitude_ratios.png',
            'plot_field': 'plots/dss_field.png'
        }
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['step'] = 'Pipeline completed successfully'
        
    except subprocess.TimeoutExpired:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = 'Pipeline timeout (>5 minutes)'
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/start_pipeline', methods=['POST'])
def start_pipeline():
    """Start the photometry pipeline."""
    data = request.json
    
    # Validate input
    required_fields = ['target_name', 'mjd_min', 'mjd_max', 'target_ra', 'target_dec',
                      'comp1_ra', 'comp1_dec', 'comp2_ra', 'comp2_dec']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create objects.dat content
    objects_data = f"""Target,{data['target_ra']},{data['target_dec']}
Comp1,{data['comp1_ra']},{data['comp1_dec']}
Comp2,{data['comp2_ra']},{data['comp2_dec']}
"""
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'step': 'Initializing',
        'target_name': data['target_name'],
        'created_at': datetime.now().isoformat()
    }
    
    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, data['target_name'], data['mjd_min'], data['mjd_max'],
              data.get('filter', 'all'), objects_data)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    """Get job status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])


@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a result file."""
    if not os.path.exists(filename):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filename, as_attachment=True)


@app.route('/plots/<path:filename>')
def serve_plot(filename):
    """Serve plot images."""
    return send_from_directory('plots', filename)


@app.route('/api/available_filters')
def available_filters():
    """Get list of common BHTOM filters."""
    filters = [
        {'value': 'all', 'label': 'All filters'},
        {'value': 'GaiaSP/R', 'label': 'GaiaSP/R (Red)'},
        {'value': 'GaiaSP/g', 'label': 'GaiaSP/g (Green)'},
        {'value': 'GaiaSP/i', 'label': 'GaiaSP/i (Near-IR)'},
        {'value': 'GaiaSP/V', 'label': 'GaiaSP/V (Visual)'},
    ]
    return jsonify(filters)


if __name__ == '__main__':
    print("=" * 70)
    print("BHTOM Photometry Web Interface")
    print("=" * 70)
    print("\nStarting Flask server...")
    print("Access the interface at: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5001)
