# Enhanced Khan Academy Question Scraper

A comprehensive, fully automated solution for downloading Khan Academy questions in their proper JSON format without any download limits.

## 🚀 Features

- **Unlimited Question Downloads**: No artificial limits on question capture
- **Automatic Question Progression**: Automatically moves through questions without manual refresh
- **Proper JSON Format**: Downloads questions in the correct Perseus format with all components
- **Enhanced Reliability**: Multiple fallback methods for question extraction
- **Browser Automation**: Automatically navigates and interacts with Khan Academy
- **Real-time Progress Monitoring**: See capture progress as it happens
- **Error Recovery**: Robust error handling and retry mechanisms

## 🛠️ Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome WebDriver** (for browser automation):
   - The script will automatically download the appropriate Chrome driver
   - Ensure Google Chrome is installed on your system

3. **Install mitmproxy certificates** (first time only):
   ```bash
   mitmdump
   # Press Ctrl+C to stop after certificates are generated
   ```

## 📋 Usage

### Method 1: Using the Enhanced Script (Recommended)

```bash
python enhanced_khan_scraper.py "https://www.khanacademy.org/math/algebra/..." 1000 60
```

**Parameters:**
- `exercise_url`: Khan Academy exercise URL (required)
- `max_questions`: Maximum questions to capture (default: 1000)
- `timeout_minutes`: Maximum time to run in minutes (default: 60)

### Method 2: Using the Batch File (Windows)

```bash
run_enhanced_scraper.bat "https://www.khanacademy.org/math/algebra/..." 1000 60
```

### Method 3: Manual Components

If you prefer to run components separately:

1. **Start the mitmproxy addon**:
   ```bash
   mitmdump -s capture_khan_json_automated.py
   ```

2. **Run browser automation** (separate terminal):
   ```bash
   python browser_automation.py
   ```

## 🔧 Key Improvements Made

### 1. Fixed JSON Extraction Issue
- **Problem**: Downloaded JSON was not the actual question content
- **Solution**: Enhanced extraction logic with multiple fallback methods
- **Result**: Now properly extracts Perseus format questions with all components

### 2. Automatic Question Progression
- **Problem**: Scraper didn't move to second question automatically
- **Solution**: Added intelligent question progression and answer simulation
- **Result**: Continuously captures new questions without manual intervention

### 3. Unlimited Question Downloading
- **Problem**: Download limits prevented capturing all questions
- **Solution**: Removed artificial limits and added continuous discovery
- **Result**: Can capture up to 1000+ questions (configurable)

### 4. Enhanced Browser Automation
- **Problem**: Browser automation wasn't working reliably
- **Solution**: Improved interaction logic and error handling
- **Result**: Robust automatic browsing and content extraction

## 📁 Output Format

Questions are saved in the `khan_academy_json/` directory with filenames like `x4199a21da4572c96.json`.

Each JSON file contains the complete Perseus question format:
```json
{
    "question": {
        "content": "Question text with LaTeX...",
        "widgets": { ... }
    },
    "hints": [ ... ],
    "answerArea": { ... }
}
```

## 🔍 How It Works

1. **mitmproxy Integration**: Intercepts HTTP requests to capture question data
2. **Browser Automation**: Automatically navigates Khan Academy exercises
3. **Question Discovery**: Identifies new question IDs from API responses
4. **Parallel Processing**: Downloads questions in batches for efficiency
5. **Data Validation**: Ensures captured data is valid Perseus format
6. **Progress Tracking**: Real-time monitoring and logging

## 🛡️ Error Handling

- **Network Issues**: Automatic retries with exponential backoff
- **Invalid Data**: Validation checks before saving
- **Browser Crashes**: Automatic browser restart
- **Proxy Issues**: Enhanced SSL/certificate handling

## 📊 Performance

- **Batch Processing**: Processes 3-5 questions simultaneously
- **Smart Delays**: Prevents rate limiting with configurable delays
- **Memory Efficient**: Streams large responses instead of loading all in memory
- **Concurrent Operations**: Browser and API requests run in parallel

## 🐛 Troubleshooting

### Common Issues:

1. **Certificate Errors**:
   ```bash
   # Run mitmproxy once to generate certificates
   mitmdump
   ```

2. **Chrome Driver Issues**:
   ```bash
   # Update Chrome and restart the script
   ```

3. **Permission Errors**:
   ```bash
   # Run as administrator on Windows
   ```

4. **Network Timeouts**:
   - Check internet connection
   - Increase timeout values in the script

## 📝 Configuration

You can modify these parameters in the script files:

- `MAX_QUESTIONS`: Maximum questions to capture (default: 1000)
- `REQUEST_DELAY`: Delay between requests (default: 1.0 seconds)
- `BATCH_SIZE`: Questions processed simultaneously (default: 3)
- `MAX_RETRIES`: Retry attempts for failed requests (default: 5)

## 🎯 Success Indicators

Look for these messages to confirm everything is working:

- `✓ Auto-captured: x4199a21da4572c96 (attempt 1)`
- `💾 Saved! Total: 15/1000 (2024-09-13 14:30:25)`
- `Progress: 50/1000 questions captured`
- `Progressed using: button[data-test-id='next-question']`

## 📈 Expected Results

With the enhanced solution, you should see:
- Continuous question capture without manual intervention
- Proper Perseus JSON format for all questions
- Automatic progression through multiple questions
- No artificial download limits
- Real-time progress monitoring

The script will automatically handle question discovery, progression, and downloading until the specified limit is reached or timeout occurs.