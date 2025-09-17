# Khan Academy Automated Question Scraper

This implementation follows the technical plan for creating a fully automated Khan Academy question scraper with three sequential parts:

## Features

- **Part 1: Automating Navigation** - Eliminates manual refreshes using Selenium WebDriver
- **Part 2: Active Batch Scraping** - Proactively downloads all question JSONs when question list is discovered
- **Part 3: Full Automation** - Complete integration with master runner script

## Files Structure

### Core Implementation Files (Per Technical Plan)
- `automate_exercise.py` - Simple browser automation for answering questions
- `capture_khan_json.py` - Enhanced mitmproxy script with active batch scraping
- `main.py` - Master runner that orchestrates mitmproxy and Selenium

### Existing Advanced Files
- `browser_automation.py` - Enhanced browser automation with advanced features
- `enhanced_khan_scraper.py` - Complete solution with autonomous capabilities
- `autonomous_scraper.py` - Full automation controller
- `active_scraper.py` - Advanced active scraping with async requests
- `capture_khan_json_automated.py` - Full-featured capture script

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Test the implementation:
```bash
python test_implementation.py
```

## Usage

### Simple Usage (Per Technical Plan)
```bash
python main.py
```

### With Custom URL and Question Limit
```bash
python main.py "https://www.khanacademy.org/math/..." 50
```

### Advanced Usage (Existing Features)
```bash
python enhanced_khan_scraper.py
```

## How It Works

### Part 1: Browser Automation
- Uses Selenium WebDriver with webdriver-manager for easy setup
- Configures Chrome to use mitmproxy for traffic interception
- Automatically answers questions with simple logic (selects first option or enters "1")
- Handles pop-ups and continues to next questions

### Part 2: Active Batch Scraping
- Captures `getOrCreatePracticeTask` responses to extract question IDs
- Immediately makes its own GraphQL requests to download all question JSONs
- Uses proper session headers and cookies for authenticated requests
- Saves Perseus data as formatted JSON files

### Part 3: Full Integration
- Master script starts mitmproxy in background
- Launches browser automation
- Handles cleanup and error scenarios
- Supports command-line arguments for customization

## Technical Details

### Proxy Configuration
- Default proxy port: 8080
- Automatically configures Chrome to use mitmproxy
- Handles SSL certificate issues for HTTPS interception

### Question Detection
- Monitors GraphQL traffic for question manifests
- Extracts question IDs from various response formats
- Active fetching prevents waiting for manual navigation

### Error Handling
- Robust element detection with multiple selectors
- Graceful handling of different question types
- Automatic retry logic for failed requests

## Output

Questions are saved as JSON files in the `khan_academy_json/` directory with the format:
- Filename: `{question_id}.json`
- Content: Perseus question data with full formatting

## Troubleshooting

1. **mitmproxy not found**: Install with `pip install mitmproxy`
2. **Chrome driver issues**: The script automatically downloads the correct driver
3. **SSL certificate errors**: Handled automatically by proxy configuration
4. **Question detection failures**: Script includes fallback parsing methods

## Architecture

The implementation provides both simple (per technical plan) and advanced versions:

- **Simple**: Direct implementation of the 3-part technical plan
- **Advanced**: Enhanced version with async processing, better error handling, and autonomous features

Both versions are compatible and can be used independently based on your needs.