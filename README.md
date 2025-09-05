# Khan Academy Question Bank Scraper

A Python-based tool that captures Khan Academy exercise questions in Perseus JSON format using mitmproxy. This tool intercepts network traffic to extract the structured question data that Khan Academy uses internally.

## Overview

Khan Academy uses the Perseus format (developed internally) to represent interactive math and science questions. This scraper captures that data by:

1. Setting up a local proxy server using mitmproxy
2. Intercepting Khan Academy API calls when you solve practice problems
3. Extracting and saving Perseus JSON data for each question

## What Gets Captured

The tool captures the complete Perseus JSON structure for each question, including:

- **Question content** with LaTeX math expressions
- **Widget definitions** (multiple-choice, numeric-input, graphing, etc.)
- **Answer validation data** (correct answers, acceptable ranges)
- **Hint sequences** for step-by-step guidance
- **Image references** and mathematical notation

### Sample Widget Types Captured
- `radio` - Multiple choice questions
- `numeric-input` - Number entry with validation
- `image` - Static images and diagrams  
- `dropdown` - Dropdown selection menus
- `matcher` - Drag-and-drop matching exercises
- `interactive-graph` - Graphing and coordinate exercises
- `expression` - Mathematical expression input
- And many more Perseus widget types...

## Prerequisites

- **Python 3.7+**
- **Google Chrome** (for browsing Khan Academy)
- **macOS** (script uses `networksetup` command for proxy configuration)

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd questionbankscrapper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   mitmdump --version
   ```

## Usage

### Quick Start

1. **Run the capture script**
   ```bash
   ./run_capture.sh
   ```

2. **Follow the automated steps:**
   - Chrome will open to Khan Academy with proxy settings configured
   - Your system proxy will be automatically set to route through mitmproxy
   - You'll see status messages in the terminal

3. **Start capturing questions:**
   - Navigate to any Khan Academy math exercise
   - Begin solving practice problems
   - Each question you encounter will be automatically captured and saved

4. **Stop when done:**
   - Press `Ctrl+C` in the terminal
   - System proxy settings will be automatically restored

### Example Capture Session

```
$ ./run_capture.sh
------------------------------------------------------------------
Khan Academy Question Bank Scraper  
------------------------------------------------------------------
[INFO] This tool captures Perseus JSON data from Khan Academy exercises.
       Follow these steps:

1. Chrome will open to Khan Academy
2. Navigate to any math exercise (e.g., practice problems)  
3. Start answering questions - they'll be captured automatically
4. Press Ctrl+C here when done

Captured questions will be saved in: khan_academy_json/
------------------------------------------------------------------

[INFO] Setting up proxy for 'Wi-Fi'...
[INFO] Launching Chrome with proxy settings...
[INFO] Starting mitmproxy capture...
       Waiting for you to start an exercise...

[INFO] Practice Task detected. Building list of questions to capture...
[INFO] Built list of 12 questions. As you answer them, they will be saved.
  -> Captured! Total: 1 (2024-09-05 14:32:15)
  -> Captured! Total: 2 (2024-09-05 14:33:22)
  -> Captured! Total: 3 (2024-09-05 14:34:18)
...
```

## Output Structure

Captured questions are saved in the `khan_academy_json/` directory with filenames based on Khan Academy's internal question IDs:

```
khan_academy_json/
├── xa1b2c3d4e5f6789.json
├── xf9e8d7c6b5a4321.json  
├── x123456789abcdef.json
└── ...
```

Each JSON file contains the complete Perseus question structure. Here's an example from the included samples:

```json
{
  "answerArea": {
    "calculator": false,
    "chi2Table": false,
    "periodicTable": false,
    "tTable": false,
    "zTable": false
  },
  "question": {
    "content": "**Complete the table to make three equivalent expressions.**\n\n[[☃ numeric-input 7]] $\\times8$ |\n$8+8$ |\n$2{}$ [[☃ dropdown 4]]  |",
    "images": {},
    "widgets": {
      "numeric-input 7": {
        "type": "numeric-input",
        "alignment": "default",
        "options": {
          "answers": [
            {
              "value": 2,
              "status": "correct",
              "maxError": null,
              "strict": false,
              "simplify": "required"
            }
          ]
        }
      },
      "dropdown 4": {
        "type": "dropdown",
        "options": {
          "choices": [
            {"content": "eights", "correct": true},
            {"content": "twos", "correct": false},
            {"content": "fours", "correct": false}
          ]
        }
      }
    }
  },
  "hints": [
    {
      "content": "$\\overset{\\greenD1}{\\blueD{8}} + \\overset{\\greenD2}{\\blueD{8}}$ is the same as $\\green2\\blueD{\\text{ eights}}$.",
      "images": {},
      "widgets": {}
    }
  ]
}
```

### Sample Questions Included

This repository includes 4 sample Khan Academy questions in the `khan_academy_json/` folder, demonstrating different widget types:
- **x0c8212a5c8672866.json**: Numeric input + dropdown widgets with LaTeX math
- **x301c5c7ddfd5ee0b.json**: Radio (multiple choice) widget with images  
- **xde44600a58981221.json**: Matcher widget for drag-and-drop pairing
- **x4199a21da4572c96.json**: Multiple image widgets with mathematical content

### Development History

See `INVESTIGATION_LOG.md` for detailed development history, including:
- API endpoint discovery process
- mitmproxy configuration challenges
- Perseus JSON structure analysis
- Widget type identification and cataloging
- Technical decisions and troubleshooting steps

This log provides valuable context for understanding how the scraper was developed and can guide future enhancements.

## Configuration

### Network Settings
The script automatically configures your system proxy settings. You can modify these in `run_capture.sh`:

```bash
PROXY_PORT="8080"           # mitmproxy listening port
PROXY_HOST="127.0.0.1"      # localhost
NETWORK_SERVICE="Wi-Fi"     # your network interface
```

### Chrome Profile
By default, the script opens a specific Chrome profile to avoid interfering with your regular browsing:

```bash  
CHROME_PROFILE_NAME="Profile 1"
```

### Output Directory
Questions are saved to the `khan_academy_json/` directory. You can change this in `capture_khan_json.py`:

```python
SAVE_DIRECTORY = "khan_academy_json"
```

## How It Works

### Technical Details

1. **Proxy Interception**: mitmproxy creates a local HTTP/HTTPS proxy server
2. **Traffic Analysis**: The script monitors specific Khan Academy API endpoints:
   - `getOrCreatePracticeTask` - Captures the list of questions in an exercise
   - `getAssessmentItem` - Captures individual question data as you encounter them
3. **Data Extraction**: Perseus JSON is extracted from the API response and saved locally
4. **Automatic Cleanup**: System proxy settings are restored when you exit

### API Endpoints Monitored

- **Practice Task Endpoint**: `api/internal/graphql/getOrCreatePracticeTask`
  - Provides the manifest of questions in an exercise session
  - Builds the list of question IDs to capture

- **Assessment Item Endpoint**: `api/internal/graphql/getAssessmentItem`  
  - Returns the complete Perseus JSON for individual questions
  - Triggered when you view/answer each question

## Troubleshooting

### Common Issues

**1. "mitmdump: command not found"**
```bash
pip install mitmproxy
```

**2. Chrome doesn't use proxy settings**
- Try restarting Chrome completely
- Check that system proxy is set: System Preferences > Network > Advanced > Proxies

**3. No questions being captured**
- Make sure you're on Khan Academy practice exercises (not videos or articles)
- Verify the terminal shows "Practice Task detected" message
- Try refreshing the exercise page

**4. Permission denied on script execution**
```bash
chmod +x run_capture.sh
```

**5. Proxy cleanup issues**
If proxy settings aren't restored properly:
```bash
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off
```

### Debugging

Enable verbose mitmproxy logging by modifying the last line in `run_capture.sh`:
```bash
mitmdump -v -s capture_khan_json.py --listen-port "$PROXY_PORT"
```

## Limitations

- **macOS Only**: Uses `networksetup` command for proxy configuration
- **Chrome Required**: Script is configured for Chrome browser
- **Perseus Format Only**: Only captures Perseus-formatted questions (not video content)
- **Network Dependent**: Requires stable internet connection to Khan Academy

## Legal Considerations

This tool is designed for educational and research purposes. Be sure to:

- Respect Khan Academy's Terms of Service
- Use captured data responsibly  
- Don't redistribute copyrighted content
- Consider reaching out to Khan Academy for official API access if doing large-scale research

## Advanced Usage

### Custom Question Selection

You can modify `capture_khan_json.py` to filter specific question types:

```python
def handle_assessment_item(self, flow: http.HTTPFlow):
    # Add filtering logic here
    item = data['data']['assessmentItem']['item']
    
    # Example: Only capture multiple choice questions
    if 'radio' in item['itemData']:
        # Save the question
        pass
```

### Bulk Processing

For processing multiple exercises:

1. Run the capture tool
2. Complete one full exercise session
3. Navigate to a new exercise type  
4. Repeat until you have desired coverage

### Data Analysis

The captured JSON files can be analyzed for:
- Question difficulty patterns
- Widget type distribution  
- Common mathematical topics
- Hint effectiveness strategies

## Development

### Project Structure
```
questionbankscrapper/
├── capture_khan_json.py    # Main mitmproxy addon
├── run_capture.sh          # Automated setup script
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── INVESTIGATION_LOG.md    # Development history and technical details
├── LICENSE                # MIT license
├── setup.py               # Python package configuration
└── khan_academy_json/     # Sample questions + captured output
    ├── x0c8212a5c8672866.json
    ├── x301c5c7ddfd5ee0b.json
    ├── xde44600a58981221.json
    └── x4199a21da4572c96.json
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational purposes. Please respect Khan Academy's intellectual property and terms of service.

---

**Need help?** Open an issue on the repository or check the troubleshooting section above.