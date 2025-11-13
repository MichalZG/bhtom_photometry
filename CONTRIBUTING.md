# Contributing to BHTOM Differential Photometry Pipeline

Thank you for your interest in contributing to this project! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Example data if possible

### Suggesting Features

Feature requests are welcome! Please open an issue describing:
- The feature you'd like to see
- Why it would be useful
- Potential implementation approach (optional)

### Code Contributions

1. **Fork the repository**
2. **Create a new branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes:**
   - Follow the existing code style
   - Add docstrings to new functions
   - Include comments for complex logic
   - Update documentation if needed

4. **Test your changes:**
   - Test with real BHTOM data
   - Verify plots are generated correctly
   - Check that output files have correct format

5. **Commit your changes:**
   ```bash
   git commit -m "Add feature: brief description"
   ```

6. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** with:
   - Clear description of changes
   - Reference to related issues
   - Example output if applicable

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Keep functions focused and concise
- Add type hints where appropriate
- Use docstrings (NumPy style preferred)

Example:
```python
def process_photometry(data: pd.DataFrame, max_distance: float = 5.0) -> pd.DataFrame:
    """
    Process photometry data with cross-matching.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input photometry data
    max_distance : float, optional
        Maximum matching radius in arcsec (default: 5.0)
        
    Returns
    -------
    pd.DataFrame
        Processed photometry results
    """
```

## Areas for Contribution

We especially welcome contributions in:

- **Additional photometry methods** (e.g., ensemble photometry)
- **Automated comparison star selection** using catalog queries
- **Multi-filter analysis** support
- **Quality metrics** and outlier detection
- **Performance optimization** for large datasets
- **Documentation improvements**
- **Test suite** development
- **Example notebooks** with real data

## Questions?

Feel free to open an issue for any questions about contributing!

Thank you for helping improve this project! 🙏
