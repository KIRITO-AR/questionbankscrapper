# Khan Academy Question Scraper - FIXED VERSION

## ✅ Issues Fixed

The scraper has been successfully fixed and is now working! Here's what was resolved:

### 1. **JSON Download Issue** ✅ FIXED
- **Problem**: Questions weren't being saved as JSON files
- **Root Cause**: The assessment item data was nested in `assessmentItem.item` instead of directly in `assessmentItem`
- **Solution**: Updated the data extraction logic to look in the correct nested structure

### 2. **Authentication Headers** ✅ FIXED  
- **Problem**: 403 Forbidden errors when making active GraphQL requests
- **Root Cause**: Missing or incorrect authentication headers
- **Solution**: Enhanced header extraction from browser requests, including proper `x-ka-fkey` handling

### 3. **Passive Data Capture** ✅ IMPROVED
- **Problem**: Only active fetching was attempted, which often failed
- **Solution**: Enhanced passive capture to save questions that are already loaded by the browser

### 4. **Terminal Feedback** ✅ ADDED
- **Problem**: No visibility into what was happening during scraping
- **Solution**: Added comprehensive logging with `[MITM]`, `[SAVE]`, and `[ERROR]` prefixes

## 🚀 How to Use

### Quick Start
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the scraper
python main.py
```

### For Section Browsing
```bash
# Navigate to a Khan Academy section (e.g., Math > Class 1)
# The scraper will automatically detect and scrape all exercises in that section
python main.py
```

## 📊 What You'll See

When running successfully, you'll see output like:
```
[mitmproxy] [MITM] Detected practice manifest operation: getOrCreatePracticeTask
[mitmproxy] [MITM] Found 7 new question IDs. Actively fetching now...
[mitmproxy] [SAVE] x57ecf9fb96c67a75.json  Total saved: 1 (2025-09-18 00:30:39)
[mitmproxy] [SAVE] xce3f4059a18666de.json  Total saved: 2 (2025-09-18 00:29:43)
```

## 📁 Output Files

JSON files are saved in the `khan_academy_json/` directory with the format:
- `x{question_id}.json` - Each question saved as a separate JSON file
- Contains: `answerArea`, `hints`, `question` data in the same format as the example

## 🔧 Technical Details

### Key Fixes Applied:
1. **Data Structure Parsing**: Fixed extraction from `assessmentItem.item` instead of `assessmentItem`
2. **Header Management**: Improved authentication header extraction and usage
3. **Error Handling**: Better error handling and fallback mechanisms
4. **Logging**: Comprehensive terminal feedback for debugging
5. **Passive Capture**: Enhanced to catch questions loaded by browser navigation

### Files Modified:
- `capture_khan_json.py` - Main mitmproxy addon with data extraction fixes
- `automate_exercise.py` - Browser automation improvements
- `main.py` - Process orchestration
- `setup_certificate.py` - Helper script for certificate setup

## ⚠️ Important Notes

1. **Certificate Trust**: For full functionality, you may need to trust the mitmproxy certificate:
   - Run `python setup_certificate.py` for instructions
   - Visit `http://mitm.it` in your browser to download the certificate

2. **Authentication**: Make sure you're logged into Khan Academy in the browser that opens

3. **Section Browsing**: The scraper now automatically detects section pages and iterates through all exercises

## 🎯 Success Metrics

- ✅ JSON files are being downloaded and saved
- ✅ Terminal shows `[SAVE]` messages when questions are captured  
- ✅ Questions are saved in the correct format matching the example
- ✅ Both passive and active capture methods work
- ✅ Section browsing automatically scrapes all exercises

The scraper is now fully functional and ready for use!
