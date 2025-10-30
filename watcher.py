import os
import time
import json
import requests
from collections import deque
from datetime import datetime

# Environment variables
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
ERROR_RATE_THRESHOLD = float(os.getenv('ERROR_RATE_THRESHOLD', 2))
WINDOW_SIZE = int(os.getenv('WINDOW_SIZE', 200))
ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN_SEC', 300))
LOG_FILE = '/var/log/nginx/access.log'

# State tracking
last_pool = None
request_window = deque(maxlen=WINDOW_SIZE)
last_alert_time = {}

def send_slack_alert(message, alert_type):
    """Send alert to Slack with cooldown"""
    current_time = time.time()
    
    # Check cooldown
    if alert_type in last_alert_time:
        time_since_last = current_time - last_alert_time[alert_type]
        if time_since_last < ALERT_COOLDOWN_SEC:
            print(f"Alert cooldown active for {alert_type}. Skipping.")
            return
    
    # Prepare Slack message
    payload = {
        "text": f"*DevOps Alert*\n{message}\n_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print(f"Slack alert sent: {alert_type}")
            last_alert_time[alert_type] = current_time
        else:
            print(f"Failed to send Slack alert: {response.status_code}")
    except Exception as e:
        print(f"Error sending Slack alert: {e}")

def parse_log_line(line):
    """Parse custom Nginx log format"""
    try:
        # Expected format: pool=blue release=release-1.0.0 status=200 upstream=app_blue:8081
        parts = {}
        for item in line.split():
            if '=' in item:
                key, value = item.split('=', 1)
                parts[key] = value
        return parts
    except Exception as e:
        print(f"Failed to parse line: {e}")
        return None

def check_error_rate():
    """Calculate error rate over the window"""
    if len(request_window) < 10:
        return 0
    
    error_count = sum(1 for status in request_window if status >= 500)
    error_rate = (error_count / len(request_window)) * 100
    return error_rate

def tail_log():
    """Tail the log file and process lines"""
    global last_pool
    
    print(f"Watching log file: {LOG_FILE}")
    print(f"Error threshold: {ERROR_RATE_THRESHOLD}%")
    print(f"Window size: {WINDOW_SIZE} requests")
    print(f"Alert cooldown: {ALERT_COOLDOWN_SEC}s\n")
    
    # Wait for log file to exist
    while not os.path.exists(LOG_FILE):
        print(f"Waiting for log file to be created...")
        time.sleep(2)
    
    print(f"Log file found. Starting to monitor...\n")
    
    # Follow the log file from the beginning
    line_count = 0
    while True:
        try:
            with open(LOG_FILE, 'r') as f:
                # Read all existing lines first
                for line in f:
                    if not line.strip():
                        continue
                    
                    # Parse log line
                    log_data = parse_log_line(line.strip())
                    if not log_data:
                        continue
                    
                    pool = log_data.get('pool')
                    status_str = log_data.get('status', '0')
                    
                    try:
                        status = int(status_str)
                    except:
                        continue
                    
                    # Track request status
                    request_window.append(status)
                    line_count += 1
                    
                    # Check for failover
                    if pool and last_pool and pool != last_pool:
                        message = f"Failover Detected!\nPool changed: `{last_pool}` -> `{pool}`"
                        send_slack_alert(message, 'failover')
                    
                    if pool:
                        last_pool = pool
                    
                    # Check error rate
                    error_rate = check_error_rate()
                    if error_rate > ERROR_RATE_THRESHOLD:
                        message = f"High Error Rate!\nError rate: `{error_rate:.1f}%` (threshold: {ERROR_RATE_THRESHOLD}%)\nLast {len(request_window)} requests"
                        send_slack_alert(message, 'error_rate')
                
                # Wait before checking for new lines
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error reading log file: {e}")
            time.sleep(2)

if __name__ == '__main__':
    if not SLACK_WEBHOOK_URL:
        print("ERROR: SLACK_WEBHOOK_URL not set!")
        exit(1)
    
    print("Starting log watcher...\n")
    tail_log()