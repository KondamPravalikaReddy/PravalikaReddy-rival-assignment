import json
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from utils import (
    parse_timestamp, is_valid_log_entry, get_memory_tier_cost,
    calculate_severity, group_logs_by_time_window, get_hourly_key,
    is_error_status, safe_divide, round_two_decimals, safe_mean,
    safe_max, safe_min
)
from config import (
    RESPONSE_TIME_THRESHOLDS, ERROR_RATE_THRESHOLDS, COST_CONFIG,
    ANOMALY_CONFIG, DEFAULT_RATE_LIMITS, CACHING_CONFIG
)


def analyze_api_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Input validation
    if not isinstance(logs, list):
        return _empty_analysis_result("Invalid input: logs must be a list")

    if len(logs) == 0:
        return _empty_analysis_result("No logs provided")

    # Filter valid logs
    valid_logs = [log for log in logs if is_valid_log_entry(log)]
    invalid_count = len(logs) - len(valid_logs)

    # Fix here: Include _metadata even if no valid logs
    if not valid_logs:
        result = _empty_analysis_result("No valid log entries found")
        result["_metadata"] = {
            "total_log_entries": len(logs),
            "valid_entries": 0,
            "invalid_entries": invalid_count,
        }
        return result

    
    # Parse timestamps
    try:
        parsed_logs = []
        for log in valid_logs:
            log_copy = log.copy()
            log_copy["_parsed_timestamp"] = parse_timestamp(log["timestamp"])
            parsed_logs.append(log_copy)
    except (ValueError, TypeError) as e:
        return _empty_analysis_result(f"Error parsing timestamps: {str(e)}")
    
    # Sort by timestamp
    parsed_logs.sort(key=lambda x: x["_parsed_timestamp"])
    
    # Build analysis components
    summary = _build_summary(parsed_logs)
    endpoint_stats = _build_endpoint_stats(parsed_logs)
    performance_issues = _detect_performance_issues(endpoint_stats)
    recommendations = _generate_recommendations(endpoint_stats, performance_issues, summary)
    hourly_dist = _build_hourly_distribution(parsed_logs)
    top_users = _get_top_users(parsed_logs, limit=5)
    
    # Advanced features
    cost_analysis = _analyze_costs(parsed_logs, endpoint_stats)
    anomalies = _detect_anomalies(parsed_logs)
    caching_opportunities = _analyze_caching_opportunities(endpoint_stats)
    
    # Build final result
    result = {
        "summary": summary,
        "endpoint_stats": endpoint_stats,
        "performance_issues": performance_issues,
        "recommendations": recommendations,
        "hourly_distribution": hourly_dist,
        "top_users_by_requests": top_users,
        "cost_analysis": cost_analysis,
        "anomalies": anomalies,
        "caching_opportunities": caching_opportunities,
    }
    
    if invalid_count > 0:
        result["_metadata"] = {
            "total_log_entries": len(logs),
            "valid_entries": len(valid_logs),
            "invalid_entries": invalid_count,
        }
    
    return result


def _empty_analysis_result(error_message: str) -> Dict[str, Any]:
    """Return an empty analysis result structure with error."""
    return {
        "summary": {
            "total_requests": 0,
            "time_range": {"start": None, "end": None},
            "avg_response_time_ms": 0,
            "error_rate_percentage": 0,
        },
        "endpoint_stats": [],
        "performance_issues": [],
        "recommendations": [],
        "hourly_distribution": {},
        "top_users_by_requests": [],
        "cost_analysis": {
            "total_cost_usd": 0,
            "cost_breakdown": {
                "request_costs": 0,
                "execution_costs": 0,
                "memory_costs": 0,
            },
            "cost_by_endpoint": [],
            "optimization_potential_usd": 0,
        },
        "anomalies": [],
        "caching_opportunities": [],
        "_error": error_message,
    }


def _build_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build summary statistics."""
    response_times = [log["response_time_ms"] for log in logs]
    error_count = sum(1 for log in logs if is_error_status(log["status_code"]))
    
    return {
        "total_requests": len(logs),
        "time_range": {
            "start": logs[0]["timestamp"],
            "end": logs[-1]["timestamp"],
        },
        "avg_response_time_ms": round_two_decimals(safe_mean(response_times)),
        "error_rate_percentage": round_two_decimals(
            safe_divide(error_count, len(logs)) * 100
        ),
    }


def _build_endpoint_stats(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build per-endpoint statistics."""
    endpoint_data = defaultdict(lambda: {
        "response_times": [],
        "status_codes": defaultdict(int),
        "request_count": 0,
        "error_count": 0,
    })
    
    for log in logs:
        endpoint = log["endpoint"]
        endpoint_data[endpoint]["response_times"].append(log["response_time_ms"])
        endpoint_data[endpoint]["status_codes"][log["status_code"]] += 1
        endpoint_data[endpoint]["request_count"] += 1
        if is_error_status(log["status_code"]):
            endpoint_data[endpoint]["error_count"] += 1
    
    stats = []
    for endpoint, data in sorted(endpoint_data.items()):
        most_common_status = max(
            data["status_codes"].items(),
            key=lambda x: x[1]
        )[0]
        
        stats.append({
            "endpoint": endpoint,
            "request_count": data["request_count"],
            "avg_response_time_ms": round_two_decimals(safe_mean(data["response_times"])),
            "slowest_request_ms": round_two_decimals(safe_max(data["response_times"])),
            "fastest_request_ms": round_two_decimals(safe_min(data["response_times"])),
            "error_count": data["error_count"],
            "most_common_status": most_common_status,
        })
    
    return stats


def _detect_performance_issues(endpoint_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect slow endpoints and high error rates."""
    issues = []
    
    for stats in endpoint_stats:
        # Check response time
        avg_time = stats["avg_response_time_ms"]
        if avg_time >= RESPONSE_TIME_THRESHOLDS["medium"]:
            severity = calculate_severity(RESPONSE_TIME_THRESHOLDS, avg_time)
            issues.append({
                "type": "slow_endpoint",
                "endpoint": stats["endpoint"],
                "avg_response_time_ms": avg_time,
                "threshold_ms": RESPONSE_TIME_THRESHOLDS["medium"],
                "severity": severity,
            })
        
        # Check error rate
        if stats["request_count"] > 0:
            error_rate = safe_divide(stats["error_count"], stats["request_count"]) * 100
            if error_rate >= ERROR_RATE_THRESHOLDS["medium"]:
                severity = calculate_severity(ERROR_RATE_THRESHOLDS, error_rate)
                issues.append({
                    "type": "high_error_rate",
                    "endpoint": stats["endpoint"],
                    "error_rate_percentage": round_two_decimals(error_rate),
                    "severity": severity,
                })
    
    return issues


def _generate_recommendations(
    endpoint_stats: List[Dict[str, Any]],
    performance_issues: List[Dict[str, Any]],
    summary: Dict[str, Any]
) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    # Cache recommendations
    for stats in endpoint_stats:
        if stats["request_count"] > 100:
            # Estimate cache hit potential (assuming most GETs are cacheable)
            cache_potential = min(89, stats["request_count"] * 0.2)  # Rough estimate
            if cache_potential > 50:
                recommendations.append(
                    f"Consider caching for {stats['endpoint']} "
                    f"({stats['request_count']} requests, "
                    f"{int(cache_potential)}% cache-hit potential)"
                )
    
    # Performance recommendations
    for issue in performance_issues:
        if issue["type"] == "slow_endpoint":
            recommendations.append(
                f"Investigate {issue['endpoint']} performance "
                f"(avg {issue['avg_response_time_ms']}ms exceeds "
                f"{issue['threshold_ms']}ms threshold)"
            )
        elif issue["type"] == "high_error_rate":
            severity_text = f"Alert: {issue['endpoint']} has "
            severity_text += f"{issue['error_rate_percentage']}% error rate"
            if issue["severity"] == "critical":
                severity_text = f"CRITICAL: {severity_text}"
            recommendations.append(severity_text)
    
    return recommendations[:10]  # Limit to top 10


def _build_hourly_distribution(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build hourly request distribution."""
    distribution = defaultdict(int)
    
    for log in logs:
        hour_key = get_hourly_key(log["timestamp"])
        if hour_key:
            distribution[hour_key] += 1
    
    return dict(sorted(distribution.items()))


def _get_top_users(logs: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """Get top users by request count."""
    user_requests = defaultdict(int)
    
    for log in logs:
        user_requests[log["user_id"]] += 1
    
    top_users = sorted(
        user_requests.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [{"user_id": user_id, "request_count": count} for user_id, count in top_users]


def _analyze_costs(
    logs: List[Dict[str, Any]],
    endpoint_stats: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze costs based on API usage patterns."""
    config = COST_CONFIG
    
    # Calculate total cost components
    request_count = len(logs)
    request_costs = request_count * config["per_request"]
    
    total_execution_time = sum(log["response_time_ms"] for log in logs)
    execution_costs = total_execution_time * config["per_millisecond"]
    
    memory_costs = sum(
        get_memory_tier_cost(log["response_size_bytes"])
        for log in logs
    )
    
    total_cost = request_costs + execution_costs + memory_costs
    
    # Per-endpoint costs
    cost_by_endpoint = []
    for stats in endpoint_stats:
        endpoint = stats["endpoint"]
        endpoint_logs = [log for log in logs if log["endpoint"] == endpoint]
        
        ep_request_cost = len(endpoint_logs) * config["per_request"]
        ep_execution_cost = sum(
            log["response_time_ms"] * config["per_millisecond"]
            for log in endpoint_logs
        )
        ep_memory_cost = sum(
            get_memory_tier_cost(log["response_size_bytes"])
            for log in endpoint_logs
        )
        ep_total = ep_request_cost + ep_execution_cost + ep_memory_cost
        
        cost_by_endpoint.append({
            "endpoint": endpoint,
            "total_cost": round_two_decimals(ep_total),
            "cost_per_request": round_two_decimals(
                safe_divide(ep_total, stats["request_count"])
            ),
        })
    
    # Optimization potential (slow endpoints)
    optimization_potential = sum(
        cost["total_cost"] * 0.2  # 20% potential savings
        for cost in cost_by_endpoint
        if any(ep["endpoint"] == cost["endpoint"] and ep["avg_response_time_ms"] > 500
               for ep in endpoint_stats)
    )
    
    return {
        "total_cost_usd": round_two_decimals(total_cost),
        "cost_breakdown": {
            "request_costs": round_two_decimals(request_costs),
            "execution_costs": round_two_decimals(execution_costs),
            "memory_costs": round_two_decimals(memory_costs),
        },
        "cost_by_endpoint": sorted(cost_by_endpoint, key=lambda x: x["total_cost"], reverse=True),
        "optimization_potential_usd": round_two_decimals(optimization_potential),
    }


def _detect_anomalies(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect anomalies in API usage patterns."""
    anomalies = []
    config = ANOMALY_CONFIG
    
    # Group logs by time windows
    windowed_logs = group_logs_by_time_window(logs, config["error_cluster_window_minutes"])
    
    # Detect request spikes
    endpoint_rates = defaultdict(list)
    for window_key, window_logs in windowed_logs.items():
        for log in window_logs:
            endpoint = log["endpoint"]
            endpoint_rates[endpoint].append(len(window_logs))
    
    for endpoint, rates in endpoint_rates.items():
        if len(rates) > 1:
            avg_rate = sum(rates) / len(rates)
            for i, rate in enumerate(rates):
                if rate > avg_rate * config["request_spike_multiplier"]:
                    windows = sorted(windowed_logs.keys())
                    if i < len(windows):
                        anomalies.append({
                            "type": "request_spike",
                            "endpoint": endpoint,
                            "timestamp": windows[i],
                            "normal_rate": int(avg_rate),
                            "actual_rate": rate,
                            "severity": "high" if rate > avg_rate * 5 else "medium",
                        })
    
    # Detect error clusters
    for window_key, window_logs in windowed_logs.items():
        error_count = sum(1 for log in window_logs if is_error_status(log["status_code"]))
        if error_count > config["error_cluster_threshold"]:
            endpoint = window_logs[0]["endpoint"] if window_logs else "unknown"
            anomalies.append({
                "type": "error_cluster",
                "endpoint": endpoint,
                "time_window": f"{window_key}",
                "error_count": error_count,
                "severity": "critical" if error_count > 20 else "high",
            })
    
    # Detect user dominance
    total_requests = len(logs)
    user_requests = defaultdict(int)
    for log in logs:
        user_requests[log["user_id"]] += 1
    
    for user_id, count in user_requests.items():
        if count > total_requests * config["user_dominance_threshold"]:
            anomalies.append({
                "type": "user_dominance",
                "user_id": user_id,
                "request_percentage": round_two_decimals(
                    safe_divide(count, total_requests) * 100
                ),
                "severity": "high",
            })
    
    return anomalies[:20]  # Limit to top 20


def _analyze_caching_opportunities(endpoint_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which endpoints would benefit most from caching."""
    config = CACHING_CONFIG
    opportunities = []
    
    for stats in endpoint_stats:
        if stats["request_count"] >= config["min_request_frequency"]:
            # Estimate cache hit rate (simplified: assumes 80% of GET requests are cacheable)
            potential_cache_hit = min(89, int((stats["request_count"] * 0.8)))
            
            if potential_cache_hit > 50:
                requests_saved = int(stats["request_count"] * 0.7)
                cost_saving = requests_saved * 0.0001
                
                opportunities.append({
                    "endpoint": stats["endpoint"],
                    "potential_cache_hit_rate": potential_cache_hit,
                    "current_requests": stats["request_count"],
                    "potential_requests_saved": requests_saved,
                    "estimated_cost_savings_usd": round_two_decimals(cost_saving),
                    "recommended_ttl_minutes": config["default_ttl_minutes"],
                    "recommendation_confidence": "high" if stats["error_count"] == 0 else "medium",
                })
    
    opportunities.sort(key=lambda x: x["estimated_cost_savings_usd"], reverse=True)
    
    total_potential_savings = {
        "requests_eliminated": sum(o["potential_requests_saved"] for o in opportunities),
        "cost_savings_usd": round_two_decimals(
            sum(o["estimated_cost_savings_usd"] for o in opportunities)
        ),
        "performance_improvement_ms": sum(
            int(o["potential_requests_saved"] * 100)
            for o in opportunities
        ),
    }
    
    return {
        "caching_opportunities": opportunities,
        "total_potential_savings": total_potential_savings,
    }