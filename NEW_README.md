# Khan Academy Question Bank Scraper

🚀 **Fully Automated Question Extraction Tool**

A powerful Python-based tool that automatically captures Khan Academy exercise questions in Perseus JSON format. No manual interaction required - the scraper handles everything from browser automation to question downloading.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Output Format](#output-format)
- [Advanced Usage](#advanced-usage)

## ✨ Features

### 🤖 **Fully Automated Operation**
- **Zero Manual Intervention**: Just provide a URL and let it run
- **Automatic Browser Control**: Navigates and starts exercises automatically
- **Smart Question Detection**: Finds and downloads all questions in an exercise
- **Batch Processing**: Downloads multiple questions simultaneously
- **Periodic Refresh**: Automatically refreshes to capture new question variations

### ⚡ **Advanced Capabilities**
- **Async Downloads**: Fast parallel question fetching
- **Session Management**: Handles authentication automatically
- **Retry Logic**: Automatically retries failed downloads
- **Progress Monitoring**: Real-time feedback on capture progress
- **Error Recovery**: Graceful handling of network issues

### 📊 **Comprehensive Output**
- **Perseus JSON Format**: Complete question data with math expressions
- **Widget Support**: All Khan Academy question types (multiple choice, numeric input, graphing, etc.)
- **Answer Validation**: Correct answers and acceptable ranges
- **Hint Systems**: Step-by-step guidance data
- **Media References**: Images and mathematical notation

## 🔧 Prerequisites

### Required Software
- **Python 3.7+** (Python 3.8+ recommended)
- **Google Chrome** browser
- **Windows 10/11** (primary support, other platforms may work)

### Automatic Dependencies
The following will be installed automatically:
- `mitmproxy` - HTTP traffic interception
- `selenium` - Browser automation
- `aiohttp` - Async HTTP requests

## 🚀 Installation

### Method 1: Quick Setup (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vandanchopra/questionbankscrapper.git
   cd questionbankscrapper
   ```

2. **Run the setup script**:
   ```bash
   # Windows
   run_automated_scraper.bat
   ```
   The script will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Guide you through the first run

### Method 2: Manual Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vandanchopra/questionbankscrapper.git
   cd questionbankscrapper
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Test installation**:
   ```bash
   python test_improvements.py
   ```

## 🎯 Quick Start

### Step 1: Find a Khan Academy Exercise
Navigate to any Khan Academy exercise page, for example:
- Algebra: `https://www.khanacademy.org/math/algebra/.../e/quadratic_formula`
- Geometry: `https://www.khanacademy.org/math/geometry/.../e/triangle_angles`
- Calculus: `https://www.khanacademy.org/math/calculus/.../e/derivatives_basic`

### Step 2: Run the Scraper

**Option A: Using the Batch File (Windows)**
```bash
run_automated_scraper.bat
```
Then enter the exercise URL when prompted.

**Option B: Direct Command**
```bash
python automated_scraper.py "https://www.khanacademy.org/math/algebra/.../e/quadratic_formula"
```

### Step 3: Monitor Progress
The scraper will:
1. ✅ Start mitmproxy on port 8080
2. ✅ Launch Chrome with proxy settings
3. ✅ Navigate to the exercise automatically
4. ✅ Start the exercise and load questions
5. ✅ Download all questions in the background
6. ✅ Refresh periodically for new questions
7. ✅ Show real-time progress updates

### Step 4: Stop When Complete
- Press `Ctrl+C` to stop gracefully
- Questions are saved in the `khan_academy_json/` directory

## 📖 Usage

### Basic Usage
```bash
# Run with default settings
python automated_scraper.py "EXERCISE_URL"

# Use custom proxy port
python automated_scraper.py --port 8081 "EXERCISE_URL"

# Check dependencies before running
python automated_scraper.py --check-deps
```

### Testing Your Setup
```bash
# Run comprehensive tests
python test_improvements.py

# Run a quick demo
python demo_scraper.py
```

### Windows Batch File
```batch
# Simple execution
run_automated_scraper.bat

# The batch file will:
# - Check Python installation
# - Verify dependencies
# - Prompt for exercise URL
# - Run the automated scraper
```

## ⚙️ Configuration

### Proxy Settings
- **Default Port**: 8080
- **Custom Port**: Use `--port` argument
- **Host**: 127.0.0.1 (localhost)

### Browser Settings
- **Browser**: Chrome (automatic detection)
- **Proxy**: Automatically configured
- **Certificates**: Automatically handled by mitmproxy

### Output Settings
- **Directory**: `khan_academy_json/`
- **Format**: Individual JSON files per question
- **Naming**: Question ID (e.g., `x4199a21da4572c96.json`)

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Python not found"
```bash
# Solution: Install Python 3.7+
# Download from: https://python.org/downloads
# Make sure to check "Add Python to PATH"
```

#### 2. "mitmproxy not found"
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or install manually
pip install mitmproxy selenium aiohttp
```

#### 3. "Chrome not found"
```bash
# Solution: Install Google Chrome
# Download from: https://www.google.com/chrome
# Make sure Chrome is in your system PATH
```

#### 4. "Permission denied" errors
```bash
# Solution: Run as administrator (Windows)
# Or check folder permissions
```

#### 5. "No questions captured"
```bash
# Solution: Let the scraper run longer
# Some exercises take time to load questions
# Try refreshing the page manually if needed
```

### Debug Mode
```bash
# Run with verbose output
python automated_scraper.py --debug "EXERCISE_URL"

# Check specific logs
type mitmproxy.log
type chromedriver.log
```

### Getting Help
```bash
# Check all available options
python automated_scraper.py --help

# Run dependency check
python automated_scraper.py --check-deps

# Run test suite
python test_improvements.py
```

## 📁 Output Format

### Directory Structure
```
khan_academy_json/
├── x4199a21da4572c96.json    # Question 1
├── x0c8212a5c8672866.json    # Question 2
├── x301c5c7ddfd5ee0b.json    # Question 3
└── xde44600a58981221.json    # Question 4
```

### Question JSON Format
Each file contains complete Perseus question data:
```json
{
  "question": {
    "content": "Solve for $x$: $x^2 + 5x + 6 = 0$",
    "widgets": {
      "numeric-input-1": {
        "type": "numeric-input",
        "options": {
          "answers": [{"value": -2}, {"value": -3}]
        }
      }
    }
  },
  "hints": [
    "Factor the quadratic expression",
    "Use the quadratic formula if needed"
  ]
}
```

## 🚀 Advanced Usage

### Batch Processing Multiple Exercises
```bash
# Create a list of URLs
echo "https://www.khanacademy.org/math/algebra/.../e/quadratic_formula" > urls.txt
echo "https://www.khanacademy.org/math/geometry/.../e/triangle_angles" >> urls.txt

# Process each URL
for /f %i in (urls.txt) do python automated_scraper.py "%i"
```

### Custom Configuration
```python
# Create custom_config.py
class CustomConfig:
    PROXY_PORT = 8081
    SAVE_DIRECTORY = "my_questions"
    REFRESH_INTERVAL = 30
    MAX_QUESTIONS = 100

# Run with custom config
python automated_scraper.py --config custom_config.py "EXERCISE_URL"
```

### Headless Mode (No Browser Window)
```python
# Edit browser_automation.py
# Uncomment this line:
# chrome_options.add_argument('--headless')
```

### Integration with Other Tools
```python
# Use as a Python module
from automated_scraper import KhanAcademyFullAutomation

scraper = KhanAcademyFullAutomation(proxy_port=8080)
scraper.run_full_automation("EXERCISE_URL")
```

## 📊 Performance

### Typical Performance
- **Questions per minute**: 10-50 (depends on exercise complexity)
- **Concurrent downloads**: 5 questions simultaneously
- **Memory usage**: ~100-200 MB
- **Network usage**: Minimal (only question data)

### Optimization Tips
- Use a fast internet connection
- Close other browser instances
- Run on a system with adequate RAM (4GB+)
- Use SSD storage for faster file writing

## 🔒 Security & Privacy

### Data Collection
- **Only question data** is captured (no personal information)
- **No login credentials** are stored
- **Local operation** - no data sent to external servers

### Network Security
- **Local proxy only** - traffic stays on your machine
- **HTTPS support** - encrypted connections maintained
- **Certificate handling** - automatic certificate management

## 📈 Monitoring & Logs

### Real-time Monitoring
The scraper provides live updates:
```
[INFO] Starting mitmproxy on port 8080...
[INFO] Browser automation started
[PROGRESS] 5 questions captured (+2)
[PROGRESS] 8 questions captured (+3)
```

### Log Files
- `mitmproxy.log` - Network interception logs
- `chromedriver.log` - Browser automation logs
- `scraper.log` - Main application logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python test_improvements.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Khan Academy for providing excellent educational content
- mitmproxy team for the powerful HTTP interception library
- Selenium team for browser automation capabilities

---

**Happy Question Scraping! 📚🚀**

For support or questions, please open an issue on GitHub.