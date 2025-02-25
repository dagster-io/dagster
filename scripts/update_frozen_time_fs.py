import os
import re
import argparse
from datetime import datetime, timedelta

def parse_time_string(time_str):
    """Parse a human-readable time string into seconds.
    Examples: "1 hour 30 minutes", "2 days", "45 seconds"
    """
    total_seconds = 0
    # Extract all number + unit pairs
    patterns = [
        (r'(\d+)\s*(?:hour|hours|hr|hrs)', 3600),  # hours to seconds
        (r'(\d+)\s*(?:minute|minutes|min|mins)', 60),  # minutes to seconds
        (r'(\d+)\s*(?:second|seconds|sec|secs)', 1),  # seconds
        (r'(\d+)\s*(?:day|days)', 86400),  # days to seconds
        (r'(\d+)\s*(?:week|weeks)', 604800),  # weeks to seconds
    ]
    
    for pattern, multiplier in patterns:
        matches = re.findall(pattern, time_str, re.IGNORECASE)
        for match in matches:
            total_seconds += int(match) * multiplier
            
    return total_seconds

def update_timestamp(delta_str, path=None):
    """Add a time delta to the timestamp stored in the file."""
    if path is None:
        path = os.environ.get('DAGSTER_FROZEN_TIME_PATH')
        if not path:
            raise ValueError("DAGSTER_FROZEN_TIME_PATH environment variable is not set")
    
    # Parse the delta string
    delta_seconds = parse_time_string(delta_str)
    
    # Read the current timestamp
    try:
        with open(path, 'r') as f:
            current_timestamp = float(f.read().strip())
    except FileNotFoundError:
        print(f"File not found: {path}")
        return
    except ValueError:
        print(f"Invalid timestamp in file: {path}")
        return
    
    # Update the timestamp
    new_timestamp = current_timestamp + delta_seconds
    
    # Write the new timestamp back to the file
    with open(path, 'w') as f:
        f.write(str(new_timestamp))
    
    # Print information about the update
    current_time = datetime.fromtimestamp(current_timestamp)
    new_time = datetime.fromtimestamp(new_timestamp)
    print(f"Updated timestamp:")
    print(f"  From: {current_timestamp} ({current_time})")
    print(f"  To:   {new_timestamp} ({new_time})")
    print(f"  Delta: {delta_str} ({delta_seconds} seconds)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update a timestamp by adding a time delta")
    parser.add_argument("delta", help="Time delta in human readable format (e.g., '1 hour 30 minutes')")
    parser.add_argument("--path", help="Path to the timestamp file (defaults to DAGSTER_FROZEN_TIME_PATH env var)")
    
    args = parser.parse_args()
    update_timestamp(args.delta, args.path)