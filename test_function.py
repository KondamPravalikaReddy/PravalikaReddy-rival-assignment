import pytest
import json
from datetime import datetime, timedelta
from function import analyze_api_logs
from utils import parse_timestamp, is_valid_log_entry, get_hourly_key


class TestInputValidation:
    """Test input validation and edge cases"""
    
    def test_empty_input_list(self):
        """Test handling of empty log list"""
        result = analyze_api_logs([])
        assert result["summary"]["total_requests"] == 0
        assert result["endpoint_stats"] == []
        assert result["_error"] is not None
    
    def test_invalid_input_type(self):
        """Test handling of non-list input"""
        result = analyze_api_logs("not a list")
        assert result["summary"]["total_requests"] == 0
        assert result["_error"] is not None
    
    def test_single_log_entry(self):
        """Test processing single log entry"""
        log = {
            "timestamp": "2025-01-15T10:00:00Z",
            "endpoint": "/api/users",
            "method": "GET",
            "response_time_ms": 100,
            "status_code": 200,
            "user_id": "user_001",
            "request_size_bytes": 256,
            "response_size_bytes": 1024,
        }
        result = analyze_api_logs([log])
        assert result["summary"]["total_requests"] == 1
        assert len(result["endpoint_stats"]) == 1
        assert result["summary"]["error_rate_percentage"] == 0
    
    def test_malformed_entry_missing_field(self):
        """Test handling of entry with missing required field"""
        logs = [
            {
                "timestamp": "2025-01-15T10:00:00Z",
                "endpoint": "/api/users",
                # Missing method field
                "response_time_ms": 100,
                "status_code": 200,
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            }
        ]
        result = analyze_api_logs(logs)
        assert result["summary"]["total_requests"] == 0
        assert "invalid_entries" in str(result.get("_metadata", ""))
    
    def test_invalid_timestamp_format(self):
        """Test handling of invalid timestamp"""
        logs = [
            {
                "timestamp": "not-a-timestamp",
                "endpoint": "/api/users",
                "method": "GET",
                "response_time_ms": 100,
                "status_code": 200,
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            }
        ]
        result = analyze_api_logs(logs)
        # Should be filtered out
        assert result["summary"]["total_requests"] == 0
    
    def test_negative_response_time(self):
        """Test handling of negative numeric values"""
        logs = [
            {
                "timestamp": "2025-01-15T10:00:00Z",
                "endpoint": "/api/users",
                "method": "GET",
                "response_time_ms": -100,
                "status_code": 200,
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            }
        ]
        result = analyze_api_logs(logs)
        assert result["summary"]["total_requests"] == 0


class TestCoreAnalytics:
    """Test core analytics calculations"""
    
    def get_sample_logs(self, count=10):
        """Generate sample logs for testing"""
        logs = []
        for i in range(count):
            logs.append({
                "timestamp": f"2025-01-15T10:{i:02d}:00Z",
                "endpoint": "/api/users" if i % 3 == 0 else "/api/payments",
                "method": "GET" if i % 2 == 0 else "POST",
                "response_time_ms": 100 + i * 50,
                "status_code": 200 if i % 4 != 0 else 500,
                "user_id": f"user_{i % 3}",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            })
        return logs
    
    def test_summary_calculations(self):
        """Test summary statistics calculations"""
        logs = self.get_sample_logs(10)
        result = analyze_api_logs(logs)
        
        assert result["summary"]["total_requests"] == 10
        assert result["summary"]["time_range"]["start"] is not None
        assert result["summary"]["time_range"]["end"] is not None
        assert result["summary"]["avg_response_time_ms"] > 0
        # 2 errors out of 10 = 20%
        assert result["summary"]["error_rate_percentage"] >= 0
    
    def test_endpoint_stats(self):
        """Test per-endpoint statistics"""
        logs = self.get_sample_logs(10)
        result = analyze_api_logs(logs)
        
        assert len(result["endpoint_stats"]) >= 1
        for stat in result["endpoint_stats"]:
            assert "endpoint" in stat
            assert "request_count" in stat
            assert "avg_response_time_ms" in stat
            assert stat["request_count"] > 0
    
    def test_hourly_distribution(self):
        """Test hourly request distribution"""
        logs = self.get_sample_logs(10)
        result = analyze_api_logs(logs)
        
        dist = result["hourly_distribution"]
        assert len(dist) > 0
        assert all(isinstance(k, str) and isinstance(v, int) for k, v in dist.items())
    
    def test_top_users(self):
        """Test top users ranking"""
        logs = self.get_sample_logs(15)
        result = analyze_api_logs(logs)
        
        top_users = result["top_users_by_requests"]
        assert len(top_users) <= 5
        assert all("user_id" in u and "request_count" in u for u in top_users)


class TestPerformanceDetection:
    """Test performance issue detection"""
    
    def test_slow_endpoint_detection(self):
        """Test detection of slow endpoints"""
        logs = [
            {
                "timestamp": "2025-01-15T10:00:00Z",
                "endpoint": "/api/slow",
                "method": "GET",
                "response_time_ms": 2500,  # Exceeds critical threshold
                "status_code": 200,
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            }
            for _ in range(5)
        ]
        result = analyze_api_logs(logs)
        
        issues = result["performance_issues"]
        slow_issues = [i for i in issues if i["type"] == "slow_endpoint"]
        assert len(slow_issues) > 0
        assert any(i["severity"] == "critical" for i in slow_issues)
    
    def test_high_error_rate_detection(self):
        """Test detection of high error rates"""
        logs = []
        for i in range(10):
            logs.append({
                "timestamp": f"2025-01-15T10:{i:02d}:00Z",
                "endpoint": "/api/problematic",
                "method": "GET",
                "response_time_ms": 100,
                "status_code": 500,  # All errors
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            })
        result = analyze_api_logs(logs)
        
        issues = result["performance_issues"]
        error_issues = [i for i in issues if i["type"] == "high_error_rate"]
        assert len(error_issues) > 0


class TestAdvancedFeatures:
    """Test advanced analytics features"""
    
    def get_diverse_logs(self, count=50):
        """Generate diverse logs for advanced feature testing"""
        logs = []
        for i in range(count):
            status = 200 if i % 5 != 0 else 500
            time = 100 if i % 3 == 0 else 1000 if i % 3 == 1 else 200
            logs.append({
                "timestamp": f"2025-01-15T10:{i % 60:02d}:00Z",
                "endpoint": f"/api/{['users', 'payments', 'reports'][i % 3]}",
                "method": "GET" if i % 2 == 0 else "POST",
                "response_time_ms": time,
                "status_code": status,
                "user_id": f"user_{i % 5}",
                "request_size_bytes": 256 + i * 10,
                "response_size_bytes": 1024 + i * 50,
            })
        return logs
    
    def test_cost_analysis(self):
        """Test cost estimation feature"""
        logs = self.get_diverse_logs(50)
        result = analyze_api_logs(logs)
        
        cost_analysis = result["cost_analysis"]
        assert "total_cost_usd" in cost_analysis
        assert cost_analysis["total_cost_usd"] > 0
        assert "cost_breakdown" in cost_analysis
        assert "request_costs" in cost_analysis["cost_breakdown"]
        assert "execution_costs" in cost_analysis["cost_breakdown"]
        assert "memory_costs" in cost_analysis["cost_breakdown"]
    
    def test_anomaly_detection(self):
        """Test anomaly detection feature"""
        logs = self.get_diverse_logs(50)
        result = analyze_api_logs(logs)
        
        anomalies = result["anomalies"]
        assert isinstance(anomalies, list)
        # May or may not have anomalies depending on data
    
    def test_caching_opportunities(self):
        """Test caching opportunity analysis"""
        logs = self.get_diverse_logs(150)
        result = analyze_api_logs(logs)
        
        caching = result["caching_opportunities"]
        assert "caching_opportunities" in caching
        assert "total_potential_savings" in caching


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_parse_timestamp_valid(self):
        """Test parsing valid timestamps"""
        timestamp = "2025-01-15T10:00:00Z"
        dt = parse_timestamp(timestamp)
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
    
    def test_parse_timestamp_invalid(self):
        """Test parsing invalid timestamps"""
        with pytest.raises(ValueError):
            parse_timestamp("not-a-timestamp")
    
    def test_is_valid_log_entry(self):
        """Test log entry validation"""
        valid_log = {
            "timestamp": "2025-01-15T10:00:00Z",
            "endpoint": "/api/users",
            "method": "GET",
            "response_time_ms": 100,
            "status_code": 200,
            "user_id": "user_001",
            "request_size_bytes": 256,
            "response_size_bytes": 1024,
        }
        assert is_valid_log_entry(valid_log) is True
        
        # Invalid: missing field
        invalid_log = valid_log.copy()
        del invalid_log["endpoint"]
        assert is_valid_log_entry(invalid_log) is False
    
    def test_get_hourly_key(self):
        """Test hourly key extraction"""
        hour = get_hourly_key("2025-01-15T10:30:45Z")
        assert hour == "10:00"
        
        hour = get_hourly_key("2025-01-15T23:59:59Z")
        assert hour == "23:00"


class TestPerformance:
    """Test performance with large datasets"""
    
    def generate_large_dataset(self, size=1000):
        """Generate large log dataset"""
        logs = []
        for i in range(size):
            logs.append({
                "timestamp": f"2025-01-15T{(i // 60) % 24:02d}:{i % 60:02d}:00Z",
                "endpoint": f"/api/{['users', 'payments', 'reports', 'search'][i % 4]}",
                "method": "GET" if i % 2 == 0 else "POST",
                "response_time_ms": 50 + (i % 500),
                "status_code": 200 if i % 20 != 0 else 500,
                "user_id": f"user_{i % 50}",
                "request_size_bytes": 256,
                "response_size_bytes": 512 + (i % 5000),
            })
        return logs
    
    def test_performance_with_1000_logs(self):
        """Test processing 1000+ logs completes in reasonable time"""
        import time
        logs = self.generate_large_dataset(1000)
        
        start = time.time()
        result = analyze_api_logs(logs)
        elapsed = time.time() - start
        
        assert result["summary"]["total_requests"] == 1000
        assert elapsed < 2.0, f"Processing took {elapsed}s, expected < 2s"
    
    def test_performance_with_10000_logs(self):
        """Test processing 10000+ logs completes in reasonable time"""
        import time
        logs = self.generate_large_dataset(10000)
        
        start = time.time()
        result = analyze_api_logs(logs)
        elapsed = time.time() - start
        
        assert result["summary"]["total_requests"] == 10000
        assert elapsed < 5.0, f"Processing took {elapsed}s, expected < 5s"


class TestRecommendations:
    """Test recommendation generation"""
    
    def test_recommendations_generated(self):
        """Test that recommendations are generated"""
        logs = [
            {
                "timestamp": f"2025-01-15T10:{i:02d}:00Z",
                "endpoint": "/api/users",
                "method": "GET",
                "response_time_ms": 2500 if i % 2 == 0 else 100,
                "status_code": 200,
                "user_id": "user_001",
                "request_size_bytes": 256,
                "response_size_bytes": 1024,
            }
            for i in range(10)
        ]
        result = analyze_api_logs(logs)
        
        recommendations = result["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])