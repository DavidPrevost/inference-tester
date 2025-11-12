"""HTML report generator for test results.

Creates comprehensive HTML reports with charts and visualizations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """Generates HTML reports with visualizations."""

    @staticmethod
    def generate_report(
        test_runs: List[Dict[str, Any]],
        summary: Dict[str, Any],
        recommendations: List[str],
        output_path: Path
    ):
        """Generate a comprehensive HTML report.

        Args:
            test_runs: List of test run dictionaries
            summary: Summary statistics dictionary
            recommendations: List of recommendation strings
            output_path: Path to output HTML file
        """
        logger.info(f"Generating HTML report: {output_path}")

        # Generate report content
        html = HTMLGenerator._build_html(test_runs, summary, recommendations)

        # Write to file with UTF-8 encoding for Unicode support
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info("HTML report generated successfully")

    @staticmethod
    def _build_html(
        test_runs: List[Dict[str, Any]],
        summary: Dict[str, Any],
        recommendations: List[str]
    ) -> str:
        """Build the HTML content.

        Args:
            test_runs: List of test runs
            summary: Summary statistics
            recommendations: List of recommendations

        Returns:
            HTML string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare data for charts
        status_data = summary.get("by_status", {})
        best_configs = summary.get("best_configs", [])

        # Group test runs by model
        by_model = {}
        for run in test_runs:
            model = run.get("model_name", "Unknown")
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(run)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Inference Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 32px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 24px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}

        h3 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 20px;
        }}

        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 30px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}

        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}

        .summary-card .label {{
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card.passed {{ background: #d4edda; }}
        .summary-card.passed .value {{ color: #155724; }}

        .summary-card.failed {{ background: #f8d7da; }}
        .summary-card.failed .value {{ color: #721c24; }}

        .summary-card.skipped {{ background: #fff3cd; }}
        .summary-card.skipped .value {{ color: #856404; }}

        .recommendations {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .recommendations ul {{
            list-style: none;
            padding-left: 0;
        }}

        .recommendations li {{
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
        }}

        .recommendations li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #3498db;
            font-weight: bold;
        }}

        .best-configs {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .best-configs ul {{
            list-style: none;
            padding-left: 0;
        }}

        .best-configs li {{
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
            font-family: 'Courier New', monospace;
        }}

        .best-configs li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}

        tr:hover {{
            background: #f5f5f5;
        }}

        .status {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status.excellent {{ background: #28a745; color: white; }}
        .status.good {{ background: #5cb85c; color: white; }}
        .status.acceptable {{ background: #ffc107; color: #333; }}
        .status.poor {{ background: #fd7e14; color: white; }}
        .status.failed {{ background: #dc3545; color: white; }}
        .status.error {{ background: #6c757d; color: white; }}
        .status.skipped {{ background: #f0ad4e; color: white; }}

        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }}

        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>LLM Inference Test Report</h1>
        <div class="timestamp">Generated: {timestamp}</div>

        <h2>Executive Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="value">{summary.get('total_tests', 0)}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="summary-card passed">
                <div class="value">{summary.get('passed', 0)}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="value">{summary.get('failed', 0)}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card skipped">
                <div class="value">{summary.get('skipped', 0)}</div>
                <div class="label">Skipped</div>
            </div>
        </div>
"""

        # Add recommendations if available
        if recommendations:
            html += """
        <div class="recommendations">
            <h3>Recommendations</h3>
            <ul>
"""
            for rec in recommendations:
                html += f"                <li>{rec}</li>\n"
            html += """            </ul>
        </div>
"""

        # Add best configurations if available
        if best_configs:
            html += """
        <div class="best-configs">
            <h3>Best Performing Configurations</h3>
            <ul>
"""
            for config in best_configs:
                html += f"""                <li>{config['model']} ({config['quant']}) - {config['profile']}: {config['status']}</li>\n"""
            html += """            </ul>
        </div>
"""

        # Add status breakdown
        html += """
        <h2>Results by Status</h2>
        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
        total = summary.get('total_tests', 1)
        for status, count in sorted(status_data.items()):
            percentage = (count / total * 100) if total > 0 else 0
            html += f"""                <tr>
                    <td><span class="status {status}">{status}</span></td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
        html += """            </tbody>
        </table>
"""

        # Add detailed results by model
        html += """
        <h2>Detailed Results</h2>
"""
        for model_name, runs in sorted(by_model.items()):
            html += f"""
        <h3>{model_name}</h3>
        <table>
            <thead>
                <tr>
                    <th>Quantization</th>
                    <th>Profile</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Key Metrics</th>
                </tr>
            </thead>
            <tbody>
"""
            for run in runs:
                metrics = run.get('metrics', {})

                # Extract key metrics
                key_metrics = []
                if 'tokens_per_sec' in metrics:
                    key_metrics.append(f"TPS: {metrics['tokens_per_sec']:.1f}")
                if 'time_to_first_token' in metrics:
                    key_metrics.append(f"TTFT: {metrics['time_to_first_token']:.1f}s")
                if 'overall_accuracy' in metrics:
                    key_metrics.append(f"Accuracy: {metrics['overall_accuracy']:.1f}%")
                if 'throughput_docs_per_hour' in metrics:
                    key_metrics.append(f"Throughput: {metrics['throughput_docs_per_hour']:.1f} docs/hr")
                if 'max_successful_context' in metrics:
                    key_metrics.append(f"Max context: {int(metrics['max_successful_context'])} tokens")
                if 'avg_tokens_per_sec' in metrics:
                    key_metrics.append(f"Avg TPS: {metrics['avg_tokens_per_sec']:.1f}")

                key_metrics_str = ", ".join(key_metrics) if key_metrics else "N/A"

                html += f"""                <tr>
                    <td>{run.get('quant', 'N/A')}</td>
                    <td>{run.get('profile_name', 'N/A')}</td>
                    <td><span class="status {run.get('status', 'unknown')}">{run.get('status', 'N/A')}</span></td>
                    <td>{run.get('duration_seconds', 0):.1f}</td>
                    <td>{key_metrics_str}</td>
                </tr>
"""
            html += """            </tbody>
        </table>
"""

        # Footer
        html += """
        <div class="footer">
            <p>Generated by LLM Inference Tester v0.1.0</p>
            <p>For best results, ensure consistent testing conditions and adequate cooling.</p>
        </div>
    </div>
</body>
</html>
"""

        return html
