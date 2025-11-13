# Setup Guide for BHTOM Photometry Pipeline

## Initial Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure API Credentials

You need BHTOM API credentials to download photometry data.

#### Option A: Using config.py (Recommended for local development)

1. Copy the example configuration file:
   ```bash
   cp config.py.example config.py
   ```

2. Edit `config.py` and add your credentials:
   ```python
   BHTOM_API_TOKEN = "your_actual_token_here"
   BHTOM_CSRF_TOKEN = "your_actual_csrf_token_here"
   ```

3. **Important:** `config.py` is in `.gitignore` and will NOT be committed to version control.

#### Option B: Using Environment Variables

Set environment variables before running the scripts:

**Linux/Mac:**
```bash
export BHTOM_API_TOKEN="your_token_here"
export BHTOM_CSRF_TOKEN="your_csrf_token_here"
```

**Windows:**
```cmd
set BHTOM_API_TOKEN=your_token_here
set BHTOM_CSRF_TOKEN=your_csrf_token_here
```

### 3. Obtain API Credentials

Contact BHTOM administrators at https://bh-tom2.astrolabs.pl/ to request API access.

You will need:
- **API Token** - for authentication
- **CSRF Token** - for security

## Verification

Test your setup:

```bash
python get_data_bhtom.py --help
```

If configured correctly, you should see the help message without warnings.

## For Local Development (Current Setup)

If you're working on the original system with existing credentials:

1. Create `config.py`:
   ```bash
   cp config.py.example config.py
   ```

2. Add your existing tokens:
   ```python
   BHTOM_API_TOKEN = "dce3c28736affaa7c10ddbe29f0bfc77681fec22"
   BHTOM_CSRF_TOKEN = "uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr"
   ```

**Note:** These tokens are for your local use only and should never be committed to version control.

## Troubleshooting

### "BHTOM API credentials not found!"

This means the script couldn't find your API credentials. Make sure:
- You've created `config.py` with valid credentials, OR
- You've set the environment variables correctly

### Still having issues?

Open an issue on the project repository with details about your setup.
