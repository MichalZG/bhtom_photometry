# BHTOM Photometry Web Interface

## 🌐 Overview

This web interface provides an easy-to-use graphical frontend for the BHTOM Differential Photometry Pipeline. Users can submit jobs, monitor progress in real-time, and download results directly from their browser.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 3. Access the Interface

Open your web browser and navigate to:
- Local: `http://localhost:5000`
- Network: `http://YOUR_IP:5000`

## 📋 Features

### ✨ User-Friendly Interface
- **Form-based input**: No command-line knowledge required
- **Real-time progress**: Watch your pipeline execute step-by-step
- **Visual results**: View plots directly in the browser
- **Easy downloads**: Get your results with one click

### 🔄 Pipeline Steps

1. **Download Data**: Fetches photometry from BHTOM API
2. **Process Photometry**: Performs differential photometry analysis
3. **Generate Plots**: Creates light curves and DSS field visualization

### 📊 Input Parameters

**Required Fields:**
- **Target Name**: Object name in BHTOM (e.g., WASP-46)
- **MJD Range**: Time window for observations (MJD min/max)
- **Target Coordinates**: RA and Dec in decimal degrees
- **Comparison Stars**: Two reference stars for differential photometry

**Optional:**
- **Filter**: Specific BHTOM filter (e.g., GaiaSP/R) or all filters

### 📥 Output Files

The pipeline generates three files:

1. **photometry_results.csv**: Processed photometry data
2. **magnitude_ratios.png**: Differential light curves
3. **dss_field.png**: DSS field image with marked objects

All files can be downloaded directly from the results page.

## 🎯 Example: WASP-46 Transit

Click the "Load WASP-46 Example" button to pre-fill the form with:

- **Target**: WASP-46
- **MJD**: 60826 - 60828 (transit night)
- **Filter**: GaiaSP/R
- **Coordinates**: Pre-configured for target and comparison stars

## 🛠️ Technical Details

### Architecture

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript + CSS
- **Processing**: Background threads for pipeline execution
- **Job Management**: In-memory job queue with unique IDs

### API Endpoints

- `GET /`: Main interface
- `POST /api/start_pipeline`: Start new pipeline job
- `GET /api/job_status/<job_id>`: Check job progress
- `GET /api/download/<filename>`: Download result files
- `GET /api/available_filters`: List BHTOM filters

### File Structure

```
bhtom_photometry/
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── app.js        # JavaScript logic
├── data/                 # Downloaded data
├── output/               # Processed results
└── plots/                # Generated plots
```

## ⚙️ Configuration

### Change Port

Edit `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Enable HTTPS

For production deployment, use a WSGI server like Gunicorn with nginx:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Timeout Settings

Pipeline steps have 5-minute timeouts. To adjust, modify `subprocess.run(timeout=300)` in `app.py`.

## 🔒 Security Notes

**⚠️ Important for Production:**

1. **API Credentials**: Ensure `config.py` is properly secured
2. **File Access**: Limit download paths to prevent directory traversal
3. **Input Validation**: All user inputs are validated before processing
4. **CORS**: Enable CORS only for trusted domains
5. **Authentication**: Consider adding user authentication for public deployment

## 🐛 Troubleshooting

### Server won't start
- Check if port 5000 is available: `netstat -tuln | grep 5000`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Pipeline fails
- Verify BHTOM API credentials in `config.py`
- Check if `objects.dat`, `get_data_bhtom.py`, and `process_photometry.py` exist
- Review error messages in the web interface

### Plots don't display
- Ensure `plots/` directory exists and is writable
- Check browser console for JavaScript errors
- Verify image paths in API responses

## 📈 Performance

- **Single job at a time**: Jobs are processed sequentially
- **Typical runtime**: 2-5 minutes for 79 epochs
- **Memory usage**: ~500MB during processing

## 🔮 Future Enhancements

- [ ] Multi-user job queue
- [ ] Job history and result caching
- [ ] Interactive plot customization
- [ ] Batch processing for multiple targets
- [ ] Database storage for results
- [ ] Email notifications on completion

## 📝 License

Same license as the main BHTOM Photometry Pipeline project.

## 🙏 Acknowledgments

Built on top of the BHTOM Differential Photometry Pipeline command-line tools.
