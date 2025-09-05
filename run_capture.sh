#!/bin/bash

# Khan Academy Question Bank Scraper
# This script automates running the Khan Academy JSON capture tool using mitmproxy.

# --- Configuration ---
PROXY_PORT="8080"
PROXY_HOST="127.0.0.1"
CHROME_PROFILE_NAME="Profile 1"
NETWORK_SERVICE="Wi-Fi"

# --- Functions ---
cleanup() {
    echo ""
    echo "[INFO] Cleaning up and restoring network settings..."
    networksetup -setwebproxystate "$NETWORK_SERVICE" off >/dev/null 2>&1
    networksetup -setsecurewebproxystate "$NETWORK_SERVICE" off >/dev/null 2>&1
    echo "[INFO] System proxy for '$NETWORK_SERVICE' has been disabled."
    echo "[INFO] Cleanup complete. Exiting."
    exit 0
}

check_dependencies() {
    # Check if mitmdump is available
    if ! command -v mitmdump &> /dev/null; then
        echo "[ERROR] mitmdump is not installed or not in PATH."
        echo "        Please install mitmproxy: pip install mitmproxy"
        exit 1
    fi
    
    # Check if Python script exists
    if [ ! -f "capture_khan_json.py" ]; then
        echo "[ERROR] capture_khan_json.py not found in current directory."
        exit 1
    fi
}

trap cleanup EXIT

# --- Pre-flight checks ---
check_dependencies

# --- Instructions ---
echo "------------------------------------------------------------------"
echo "Khan Academy Question Bank Scraper"
echo "------------------------------------------------------------------"
echo "[INFO] This tool captures Perseus JSON data from Khan Academy exercises."
echo "       Follow these steps:"
echo ""
echo "1. Chrome will open to Khan Academy"
echo "2. Navigate to any math exercise (e.g., practice problems)"
echo "3. Start answering questions - they'll be captured automatically"
echo "4. Press Ctrl+C here when done"
echo ""
echo "Captured questions will be saved in: khan_academy_json/"
echo "------------------------------------------------------------------"
echo ""

# --- Main Execution ---
echo "[INFO] Setting up proxy for '$NETWORK_SERVICE'..."
networksetup -setwebproxystate "$NETWORK_SERVICE" off
networksetup -setsecurewebproxystate "$NETWORK_SERVICE" off
networksetup -setwebproxy "$NETWORK_SERVICE" "$PROXY_HOST" "$PROXY_PORT"
networksetup -setsecurewebproxy "$NETWORK_SERVICE" "$PROXY_HOST" "$PROXY_PORT"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "[INFO] Launching Chrome with proxy settings..."
open -na "Google Chrome" --args \
    --profile-directory="$CHROME_PROFILE_NAME" \
    --ignore-certificate-errors \
    --ignore-ssl-errors \
    "https://www.khanacademy.org"

echo "[INFO] Starting mitmproxy capture..."
echo "       Waiting for you to start an exercise..."
echo ""

# Run mitmdump with the capture script
mitmdump -q -s capture_khan_json.py --listen-port "$PROXY_PORT"