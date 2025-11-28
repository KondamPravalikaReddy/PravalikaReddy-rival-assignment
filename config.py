# Performance thresholds (milliseconds)
RESPONSE_TIME_THRESHOLDS = {
    "medium": 500,
    "high": 1000,
    "critical": 2000,
}

# Error rate thresholds (percentage)
ERROR_RATE_THRESHOLDS = {
    "medium": 5,
    "high": 10,
    "critical": 15,
}

# Cost configuration (USD)
COST_CONFIG = {
    "per_request": 0.0001,  # Cost per API request
    "per_millisecond": 0.000002,  # Cost per millisecond of execution
    "memory_tiers": {
        "small": {"max_bytes": 1024, "cost": 0.00001},  # 0-1KB
        "medium": {"max_bytes": 10240, "cost": 0.00005},  # 1-10KB
        "large": {"max_bytes": float('inf'), "cost": 0.0001},  # 10KB+
    },
}

# Anomaly detection thresholds
ANOMALY_CONFIG = {
    "request_spike_multiplier": 3,  # > 3x normal rate
    "response_time_degradation": 2,  # > 2x normal avg
    "error_cluster_threshold": 10,  # > 10 errors in window
    "error_cluster_window_minutes": 5,
    "user_dominance_threshold": 0.5,  # Single user > 50% of requests
}

# Rate limiting defaults
DEFAULT_RATE_LIMITS = {
    "per_user": {
        "requests_per_minute": 100,
        "requests_per_hour": 1000,
    },
    "per_endpoint": {
        "requests_per_minute": 500,
        "requests_per_hour": 5000,
    },
}

# Caching analysis thresholds
CACHING_CONFIG = {
    "min_request_frequency": 100,
    "min_get_percentage": 0.80,
    "max_error_rate": 0.02,
    "default_ttl_minutes": 15,
}

# HTTP status code ranges
ERROR_STATUS_CODES = set(range(400, 600))  # 4xx and 5xx
SUCCESS_STATUS_CODES = set(range(200, 300))  # 2xx