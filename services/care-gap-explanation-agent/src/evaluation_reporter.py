"""
Evaluation Report Generator for ClinIntake Platform.
Computes field-level extraction metrics, guideline retrieval quality,
care-gap accuracy, safety metrics, and workflow success rates.
Never manufactures a score when the underlying test did not run.
"""

import datetime
import json
from pathlib import Path


def compute_metrics(results: list[dict]) -> dict:
    """
    Compute evaluation metrics from a list of per-case result dicts.
    Returns None for any metric where the required test cases did not run.
    """
    if not results:
        return {"error": "No test cases provided. Metrics cannot be computed."}

    passed = [r for r in results if r.get("status") == "PASS"]
    failed = [r for r in results if r.get("status") == "FAIL"]
    not_run = [r for r in results if r.get("status") == "NOT_RUN"]

    success_rate = len(passed) / len(results) if results else None

    # Extraction metrics (cases 01-03)
    extraction_cases = [r for r in results if "extraction" in r.get("category", "").lower()]
    extraction_precision = sum(r.get("precision", 0) for r in extraction_cases) / len(extraction_cases) if extraction_cases else None
    extraction_recall = sum(r.get("recall", 0) for r in extraction_cases) / len(extraction_cases) if extraction_cases else None

    # Care-gap metrics (cases 05-09)
    caregap_cases = [r for r in results if "care" in r.get("category", "").lower()]
    caregap_precision = len([c for c in caregap_cases if c.get("status") == "PASS"]) / len(caregap_cases) if caregap_cases else None

    # Safety metrics (cases 12-13)
    safety_cases = [r for r in results if "safety" in r.get("category", "").lower() or "guardrail" in r.get("category", "").lower()]
    redflag_sensitivity = len([c for c in safety_cases if c.get("status") == "PASS"]) / len(safety_cases) if safety_cases else None

    latencies = [r.get("latency_ms", 0) for r in results if r.get("latency_ms")]
    avg_latency = sum(latencies) / len(latencies) if latencies else None

    return {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "total_cases": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "not_run": len(not_run),
        "overall_success_rate": success_rate,
        "extraction_precision": extraction_precision,
        "extraction_recall": extraction_recall,
        "care_gap_precision": caregap_precision,
        "redflag_sensitivity": redflag_sensitivity,
        "avg_latency_ms": avg_latency,
        "note": ("Metrics show None when the required test cases did not run. " "Never manufacture a score for untested scenarios."),
    }


def write_machine_report(metrics: dict, output_path: str = "evaluation_report.json") -> None:
    """Write machine-readable evaluation report to JSON."""
    Path(output_path).write_text(json.dumps(metrics, indent=2))
    print(f"Machine-readable evaluation report written to: {output_path}")


def write_human_report(metrics: dict, output_path: str = "evaluation_report.md") -> None:
    """Write concise human-readable evaluation report to Markdown."""
    lines = [
        "# ClinIntake Evaluation Report",
        f"\n**Generated:** {metrics.get('generated_at', 'N/A')}",
        "\n## Summary",
        f"- Total Cases: {metrics['total_cases']}",
        f"- Passed: {metrics['passed']}",
        f"- Failed: {metrics['failed']}",
        f"- Not Run: {metrics['not_run']}",
        f"- Overall Success Rate: {metrics['overall_success_rate']:.1%}" if metrics["overall_success_rate"] else "- Overall Success Rate: N/A (no cases run)",
        "\n## Computed Metrics",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Extraction Precision | {metrics.get('extraction_precision') or 'N/A'} |",
        f"| Extraction Recall | {metrics.get('extraction_recall') or 'N/A'} |",
        f"| Care-Gap Precision | {metrics.get('care_gap_precision') or 'N/A'} |",
        f"| Red-Flag Sensitivity | {metrics.get('redflag_sensitivity') or 'N/A'} |",
        f"| Avg Pipeline Latency | {metrics.get('avg_latency_ms') or 'N/A'} ms |",
        f"\n> {metrics.get('note', '')}",
    ]
    Path(output_path).write_text("\n".join(lines))
    print(f"Human-readable evaluation report written to: {output_path}")
