// BHTOM Photometry Pipeline - Web Interface JavaScript

let currentJobId = null;
let statusCheckInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadFilters();
    setupEventListeners();
});

// Load available filters
async function loadFilters() {
    try {
        const response = await fetch('/api/available_filters');
        const filters = await response.json();
        
        const select = document.getElementById('filter');
        select.innerHTML = '';
        
        filters.forEach(filter => {
            const option = document.createElement('option');
            option.value = filter.value;
            option.textContent = filter.label;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('pipeline-form').addEventListener('submit', handleSubmit);
    
    // Load example button
    document.getElementById('load-example').addEventListener('click', loadExample);
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Retry button
    document.getElementById('retry-btn').addEventListener('click', resetForm);
    
    // New analysis button
    document.getElementById('new-analysis-btn').addEventListener('click', resetForm);
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const formData = {
        target_name: document.getElementById('target_name').value,
        mjd_min: parseFloat(document.getElementById('mjd_min').value),
        mjd_max: parseFloat(document.getElementById('mjd_max').value),
        filter: document.getElementById('filter').value,
        target_ra: parseFloat(document.getElementById('target_ra').value),
        target_dec: parseFloat(document.getElementById('target_dec').value),
        comp1_ra: parseFloat(document.getElementById('comp1_ra').value),
        comp1_dec: parseFloat(document.getElementById('comp1_dec').value),
        comp2_ra: parseFloat(document.getElementById('comp2_ra').value),
        comp2_dec: parseFloat(document.getElementById('comp2_dec').value)
    };
    
    // Show progress section
    document.getElementById('input-section').style.display = 'none';
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    
    try {
        const response = await fetch('/api/start_pipeline', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to start pipeline');
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start checking status
        checkJobStatus();
        statusCheckInterval = setInterval(checkJobStatus, 2000);
        
    } catch (error) {
        showError(error.message);
    }
}

// Check job status
async function checkJobStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/api/job_status/${currentJobId}`);
        const job = await response.json();
        
        updateProgress(job);
        
        if (job.status === 'completed') {
            clearInterval(statusCheckInterval);
            showResults(job);
        } else if (job.status === 'error') {
            clearInterval(statusCheckInterval);
            showError(job.error);
        }
        
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Update progress display
function updateProgress(job) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressDetails = document.getElementById('progress-details');
    const logsWindow = document.getElementById('logs-window');
    
    let progress = 0;
    if (job.status === 'queued') progress = 10;
    else if (job.step && job.step.includes('Downloading')) progress = 30;
    else if (job.step && job.step.includes('Processing')) progress = 60;
    else if (job.step && job.step.includes('Generating')) progress = 85;
    else if (job.status === 'completed') progress = 100;
    
    progressFill.style.width = progress + '%';
    progressText.textContent = job.step || 'Processing...';
    
    // Show details
    let details = `Status: ${job.status}\n`;
    details += `Target: ${job.target_name}\n`;
    if (job.epochs_downloaded) {
        details += `Epochs downloaded: ${job.epochs_downloaded}\n`;
    }
    progressDetails.textContent = details;
    
    // Update logs
    if (job.logs && job.logs.length > 0) {
        logsWindow.textContent = job.logs.join('\n');
        // Auto-scroll to bottom
        logsWindow.scrollTop = logsWindow.scrollHeight;
    }
}

// Show results
function showResults(job) {
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    
    // Summary
    const summary = document.getElementById('results-summary');
    summary.innerHTML = `
        <h4>Pipeline completed successfully!</h4>
        <p><strong>Target:</strong> ${job.target_name}</p>
        ${job.epochs_downloaded ? `<p><strong>Epochs processed:</strong> ${job.epochs_downloaded}</p>` : ''}
        <p><strong>Completed at:</strong> ${new Date().toLocaleString()}</p>
    `;
    
    // Load plots
    if (job.files) {
        if (job.files.plot_lightcurve) {
            document.getElementById('plot-lightcurve').src = `/${job.files.plot_lightcurve}?t=${Date.now()}`;
        }
        if (job.files.plot_field) {
            document.getElementById('plot-field').src = `/${job.files.plot_field}?t=${Date.now()}`;
        }
        
        // File list
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        
        Object.entries(job.files).forEach(([key, path]) => {
            const li = document.createElement('li');
            const fileName = path.split('/').pop();
            const fileType = key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            li.innerHTML = `
                <span>📄 ${fileType}: ${fileName}</span>
                <a href="/api/download/${path}" download>Download</a>
            `;
            fileList.appendChild(li);
        });
    }
}

// Show error
function showError(message) {
    document.getElementById('input-section').style.display = 'none';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'block';
    
    document.getElementById('error-message').textContent = message;
}

// Reset form
function resetForm() {
    currentJobId = null;
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    document.getElementById('input-section').style.display = 'block';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
}

// Load WASP-46 example
function loadExample() {
    document.getElementById('target_name').value = 'WASP-46';
    document.getElementById('mjd_min').value = '60826';
    document.getElementById('mjd_max').value = '60828';
    document.getElementById('filter').value = 'GaiaSP/R';
    document.getElementById('target_ra').value = '318.7370317';
    document.getElementById('target_dec').value = '-55.8719860';
    document.getElementById('comp1_ra').value = '318.6979386';
    document.getElementById('comp1_dec').value = '-55.8612412';
    document.getElementById('comp2_ra').value = '318.6808985';
    document.getElementById('comp2_dec').value = '-55.7915780';
    
    // Show notification
    alert('WASP-46 example data loaded! Click "Start Pipeline" to begin.');
}

// Switch tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
}
