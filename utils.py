from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics

from config import ERROR_STATUS_CODES


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO 8601 timestamp string to datetime object.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp (e.g., "2025-01-15T10:00:00Z")
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        # Handle various ISO 8601 formats
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}") from e


def is_valid_log_entry(entry: Any) -> bool:
    """
    Validate a single log entry for required fields and correct types.
    
    Args:
        entry: Dictionary representing a single API log
        
    Returns:
        bool: True if entry is valid, False otherwise
    """
    if not isinstance(entry, dict):
        return False
    
    required_fields = {
        "timestamp": str,
        "endpoint": str,
        "method": str,
        "response_time_ms": (int, float),
        "status_code": int,
        "user_id": str,
        "request_size_bytes": (int, float),
        "response_size_bytes": (int, float),
    }
    
    for field, expected_type in required_fields.items():
        if field not in entry:
            return False
        
        value = entry[field]
        if not isinstance(value, expected_type):
            return False
        
        # Validate numeric fields are non-negative
        if isinstance(expected_type, tuple):
            if isinstance(value, (int, float)) and value < 0:
                return False
        elif expected_type in (int, float):
            if value < 0:
                return False
    
    # Validate timestamp format
    try:
        parse_timestamp(entry["timestamp"])
    except ValueError:
        return False
    
    return True


def get_memory_tier_cost(size_bytes: int) -> float:
    """
    Get cost for a given response size based on memory tiers.
    
    Args:
        size_bytes: Response size in bytes
        
    Returns:
        Cost in USD
    """
    from config import COST_CONFIG
    
    tiers = COST_CONFIG["memory_tiers"]
    
    if size_bytes <= tiers["small"]["max_bytes"]:
        return tiers["small"]["cost"]
    elif size_bytes <= tiers["medium"]["max_bytes"]:
        return tiers["medium"]["cost"]
    else:
        return tiers["large"]["cost"]


def calculate_severity(
    threshold_config: Dict[str, int],
    actual_value: float
) -> str:
    """
    Determine severity level based on thresholds.
    
    Args:
        threshold_config: Dict with "medium", "high", "critical" keys
        actual_value: The measured value to classify
        
    Returns:
        Severity string: "low", "medium", "high", or "critical"
    """
    if actual_value >= threshold_config["critical"]:
        return "critical"
    elif actual_value >= threshold_config["high"]:
        return "high"
    elif actual_value >= threshold_config["medium"]:
        return "medium"
    return "low"


def group_logs_by_time_window(
    logs: List[Dict[str, Any]],
    window_minutes: int
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group logs by time windows.
    
    Args:
        logs: List of log entries
        window_minutes: Size of time window in minutes
        
    Returns:
        Dict mapping time window to list of logs
    """
    grouped = defaultdict(list)
    
    for log in logs:
        try:
            dt = parse_timestamp(log["timestamp"])
            # Round down to nearest window
            window_start = dt.replace(
                minute=(dt.minute // window_minutes) * window_minutes,
                second=0,
                microsecond=0
            )
            window_key = window_start.isoformat()
            grouped[window_key].append(log)
        except (ValueError, KeyError):
            continue
    
    return dict(grouped)


def get_hourly_key(timestamp_str: str) -> Optional[str]:
    """
    Extract hour from timestamp for hourly distribution.
    
    Args:
        timestamp_str: ISO 8601 formatted timestamp
        
    Returns:
        Hour string (e.g., "10:00") or None if parsing fails
    """
    try:
        dt = parse_timestamp(timestamp_str)
        return f"{dt.hour:02d}:00"
    except (ValueError, TypeError):
        return None


def is_error_status(status_code: int) -> bool:
    """Check if status code indicates an error."""
    return status_code in ERROR_STATUS_CODES


def safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide, returning 0 if denominator is 0."""
    return numerator / denominator if denominator != 0 else 0.0


def round_two_decimals(value: float) -> float:
    """Round value to 2 decimal places."""
    return round(value, 2)


def safe_mean(values: List[float]) -> float:
    """Calculate mean safely, returning 0 for empty list."""
    return statistics.mean(values) if values else 0.0


def safe_max(values: List[float], default: float = 0) -> float:
    """Get max from list, returning default for empty list."""
    return max(values) if values else default


def safe_min(values: List[float], default: float = 0) -> float:
    """Get min from list, returning default for empty list."""
    return min(values) if values else default