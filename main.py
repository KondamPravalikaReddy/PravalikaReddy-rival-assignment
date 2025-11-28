import json
import sys
import os
from function import analyze_api_logs


def main():
    """
    Main CLI entry point.
    Usage: python main.py <log_file> [output_file]
    """
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <log_file> [output_file]")
        print()
        print("Example:")
        print("  python main.py logs.json")
        print("  python main.py logs.json output.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "analysis_result.json"
    
    # Check input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    try:
        # Load logs
        print(f"Loading logs from {input_file}...")
        with open(input_file, 'r') as f:
            logs = json.load(f)
        
        if not isinstance(logs, list):
            print("Error: Input file must contain a JSON array of logs")
            sys.exit(1)
        
        print(f"Loaded {len(logs)} log entries")
        
        # Analyze
        print("Analyzing logs...")
        result = analyze_api_logs(logs)
        
        # Save results
        print(f"Saving results to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        summary = result.get("summary", {})
        print(f"Total Requests: {summary.get('total_requests', 0)}")
        print(f"Error Rate: {summary.get('error_rate_percentage', 0)}%")
        print(f"Avg Response Time: {summary.get('avg_response_time_ms', 0)}ms")
        
        endpoints = result.get("endpoint_stats", [])
        print(f"Endpoints Analyzed: {len(endpoints)}")
        
        issues = result.get("performance_issues", [])
        print(f"Performance Issues Found: {len(issues)}")
        
        anomalies = result.get("anomalies", [])
        print(f"Anomalies Detected: {len(anomalies)}")
        
        cost_analysis = result.get("cost_analysis", {})
        print(f"Total Cost: ${cost_analysis.get('total_cost_usd', 0)}")
        
        print(f"\nResults saved to {output_file}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()