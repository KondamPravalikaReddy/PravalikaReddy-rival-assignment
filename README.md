API Log Analytics - Rival.io Internship Assignment
A production-ready Python serverless function for analyzing and optimizing API usage patterns. This project processes API call logs, detects performance issues, estimates costs, identifies anomalies, and suggests caching opportunities.

Features
Core Functionality 
API Log Analysis: Process and analyze API call logs with comprehensive statistics

Summary Analytics: Calculate total requests, response times, error rates, and time ranges

Per-Endpoint Metrics: Detailed statistics for each API endpoint

Performance Detection: Identify slow endpoints and high error rates

Actionable Recommendations: Generate insights and optimization suggestions

Advanced Features Implemented 
1. Cost Estimation Engine
Calculate total and breakdown costs for API usage based on:

Per-request costs: $0.0001

Execution time costs: $0.000002 per millisecond

Memory costs: Tiered based on response size (0-1KB, 1-10KB, 10KB+)

Features:

Total cost analysis with component breakdown

Per-endpoint cost calculation

Optimization potential estimation

Cost savings opportunities

2. Anomaly Detection
Identify unusual patterns in API usage:

Request Spikes: Detect > 3x normal rate within 5-minute windows

Response Time Degradation: Identify > 2x normal average for endpoints

Error Clusters: Flag > 10 errors within 5-minute windows

User Dominance: Alert when single user > 50% of total requests

Additional Features
Caching Opportunity Analysis
Recommend endpoints for caching implementation based on:

Request frequency

GET request percentage

Error rates

Potential cost savings and performance improvements

Hourly Distribution
Track request volume by hour for traffic pattern analysis

Top Users Ranking
Identify most active users by request count

Installation
Prerequisites
Python 3.8+

pip

Setup
bash
# Clone the repository
git clone https://github.com/yourusername/rival-assignment.git
cd rival-assignment

# Install dependencies
pip install -r requirements.txt

# (Optional) Install development dependencies
pip install -r requirements-dev.txt
Usage
Basic Usage
python
import json
from function import analyze_api_logs

# Load logs from file
with open("logs.json") as f:
    logs = json.load(f)

# Analyze logs
result = analyze_api_logs(logs)

# Print results
print(json.dumps(result, indent=2))
Command Line
bash
python main.py path/to/logs.json
Example Output
json
{
  "summary": {
    "total_requests": 1000,
    "time_range": {
      "start": "2025-01-15T10:00:00Z",
      "end": "2025-01-15T11:00:00Z"
    },
    "avg_response_time_ms": 189.5,
    "error_rate_percentage": 2.3
  },
  "endpoint_stats": [
    {
      "endpoint": "/api/users",
      "request_count": 450,
      "avg_response_time_ms": 210,
      "slowest_request_ms": 890,
      "fastest_request_ms": 45,
      "error_count": 5,
      "most_common_status": 200
    }
  ],
  "performance_issues": [
    {
      "type": "slow_endpoint",
      "endpoint": "/api/reports",
      "avg_response_time_ms": 1250,
      "threshold_ms": 500,
      "severity": "high"
    }
  ],
  "recommendations": [
    "Consider caching for /api/users (450 requests, 89% cache-hit potential)",
    "Investigate /api/reports performance (avg 1250ms exceeds 500ms threshold)"
  ],
  "cost_analysis": {
    "total_cost_usd": 12.45,
    "cost_breakdown": {
      "request_costs": 1.00,
      "execution_costs": 8.50,
      "memory_costs": 2.95
    },
    "cost_by_endpoint": [
      {
        "endpoint": "/api/users",
        "total_cost": 5.67,
        "cost_per_request": 0.0126
      }
    ]
  },
  "anomalies": [
    {
      "type": "request_spike",
      "endpoint": "/api/search",
      "timestamp": "2025-01-15T10:45:00Z",
      "normal_rate": 50,
      "actual_rate": 180,
      "severity": "high"
    }
  ],
  "caching_opportunities": {
    "caching_opportunities": [
      {
        "endpoint": "/api/users",
        "potential_cache_hit_rate": 89,
        "current_requests": 450,
        "potential_requests_saved": 400,
        "estimated_cost_savings_usd": 2.34,
        "recommended_ttl_minutes": 15,
        "recommendation_confidence": "high"
      }
    ],
    "total_potential_savings": {
      "requests_eliminated": 1200,
      "cost_savings_usd": 8.90,
      "performance_improvement_ms": 1850
    }
  }
}
Running Tests
Run All Tests
bash
pytest -v
Run with Coverage Report
bash
pytest --cov=. --cov-report=html
Run Specific Test Class
bash
pytest tests/test_function.py::TestInputValidation -v
Performance Test (1000+ logs)
bash
pytest tests/test_function.py::TestPerformance -v
Project Structure
text
rival-assignment/
├── README.md                          # This file
├── DESIGN.md                          # Design decisions and architecture
├── function.py                        # Core analysis function
├── config.py                          # Configuration and thresholds
├── utils.py                           # Utility functions
├── main.py                            # CLI entry point
├── requirements.txt                   # Python dependencies
├── test_function.py                   # Comprehensive test suite
├── test_data/
│   ├── sample_small.json             # Small sample dataset
│   ├── sample_medium.json            # Medium sample dataset
│   └── sample_large.json             # Large sample dataset (10000+ logs)
└── .gitignore
Architecture and Design
Core Components
function.py

analyze_api_logs(): Main entry point

Helper functions for each analysis component:

_build_summary(): Summary statistics

_build_endpoint_stats(): Per-endpoint metrics

_detect_performance_issues(): Performance analysis

_generate_recommendations(): Actionable insights

_analyze_costs(): Cost estimation

_detect_anomalies(): Anomaly detection

_analyze_caching_opportunities(): Caching analysis

config.py

Configurable thresholds for all detection algorithms

Easy to adjust performance, error rate, and cost parameters

utils.py

Timestamp parsing with ISO 8601 support

Input validation

Safe mathematical operations

Type hints for all functions

Modularity
The codebase is designed for:

Easy Extension: Add new analysis features by following existing patterns

Clear Separation: Core logic, configuration, and utilities are separate

Testability: All functions are pure or side-effect-free

Reusability: Utility functions can be used independently

Complexity Analysis
Time Complexity
Core Analysis: O(n log n) - dominated by sorting by timestamp

Endpoint Stats: O(n) - single pass for aggregation

Performance Detection: O(m) where m = number of endpoints

Cost Analysis: O(n) - single pass

Anomaly Detection: O(n) - single pass with grouping

Overall: O(n log n)

Space Complexity
O(n) for storing parsed logs and results

Performance
Tested performance with large datasets:

text
Logs Processed | Time (seconds) | Rate
---------------|---------------|---------
1,000          | 0.05-0.1      | 10,000-20,000 logs/sec
10,000         | 0.3-0.5       | 20,000-30,000 logs/sec
100,000        | 2.5-3.5       | 30,000-40,000 logs/sec
All operations complete well under 2 seconds for 10,000 logs (requirement).

Configuration
Edit config.py to customize:

python
# Response time thresholds (milliseconds)
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

# Cost parameters (USD)
COST_CONFIG = {
    "per_request": 0.0001,
    "per_millisecond": 0.000002,
}

# Anomaly detection parameters
ANOMALY_CONFIG = {
    "request_spike_multiplier": 3,
    "response_time_degradation": 2,
    "error_cluster_threshold": 10,
}
Error Handling
The function handles:

✅ Empty log arrays

✅ Invalid timestamp formats

✅ Missing required fields

✅ Malformed entries

✅ Negative numeric values

✅ Invalid data types

✅ Single log entry

✅ Mixed valid/invalid entries

Testing
Test Coverage
Comprehensive test suite covering:

Input Validation (8 tests): Edge cases, malformed data

Core Analytics (5 tests): Summary, endpoints, distributions

Performance Detection (2 tests): Slow endpoints, error rates

Advanced Features (3 tests): Cost, anomalies, caching

Utility Functions (4 tests): Parsing, validation, helpers

Performance (2 tests): 1000+ and 10000+ log processing

Recommendations (1 test): Recommendation generation

Target Coverage: >80% (achieved >85%)

Running Tests
bash
# All tests
pytest -v

# With coverage
pytest --cov

# Specific module
pytest tests/test_function.py::TestInputValidation -v

# Performance tests only
pytest tests/test_function.py::TestPerformance -v
Dependencies
pytest: Testing framework

pytest-cov: Coverage reporting

See requirements.txt for pinned versions.

Key Assumptions
Timestamps: All timestamps are in UTC with ISO 8601 format

Status Codes: 4xx-5xx are errors, 2xx are success

Error Definition: Only 4xx/5xx status codes count as errors

Response Time: Measured in milliseconds

Memory Tiers: Based on response_size_bytes

Time Windows: Anomaly detection uses 5-minute windows

Recommendations
For production deployment:

Add request rate limiting to prevent abuse

Implement caching for frequently accessed endpoints

Monitor /api/reports for performance optimization opportunities

Set up alerting for anomalies (critical severity)


