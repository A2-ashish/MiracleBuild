"""Analysis script to compare cost vs quality tradeoffs for the compiler pipeline."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def analyze_tradeoffs(results_path: str = "eval_results.json"):
    path = Path(__file__).parent / results_path
    
    if not path.exists():
        logger.error(f"Results file not found: {path}")
        logger.info("Please run the evaluation suite first: python -m app.evaluation.runner")
        return

    with open(path, "r") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    details = data.get("details", [])

    if not summary:
        logger.error("No summary found in results.")
        return

    print("\n" + "="*50)
    print("🌟 Miracle Build: Cost vs Quality Analysis")
    print("="*50 + "\n")

    # 1. Pipeline Reliability
    print(f"--- 1. Reliability ---")
    print(f"Overall Success Rate: {summary.get('success_rate')}% ({summary.get('successes')}/{summary.get('total')})")
    print(f"Average Repair Cycles Needed: {summary.get('avg_retries', 0):.2f}")
    if summary.get('failure_type_breakdown'):
        print(f"Failure Breakdown:")
        for k, v in summary.get('failure_type_breakdown').items():
            print(f"  - {k}: {v}")
    print()

    # 2. Performance (Latency)
    print(f"--- 2. Latency (Speed) ---")
    print(f"Average Pipeline Duration: {summary.get('avg_duration_ms', 0) / 1000:.2f}s")
    print(f"Min Duration: {summary.get('min_duration_ms', 0) / 1000:.2f}s")
    print(f"Max Duration: {summary.get('max_duration_ms', 0) / 1000:.2f}s")
    print()

    # 3. Cost Analysis
    avg_cost = summary.get('avg_cost_usd', 0)
    print(f"--- 3. Cost ---")
    print(f"Average Cost Per Compilation: ${avg_cost:.4f}")
    print(f"Cost for 1,000 compilations: ${avg_cost * 1000:.2f}")
    print(f"Cost for 10,000 compilations: ${avg_cost * 10000:.2f}")
    print(f"Average Token Usage: {summary.get('avg_tokens', 0)} tokens")
    print()

    # 4. Quality (Entities Check)
    print(f"--- 4. Quality & Completeness ---")
    print(f"Entity Check Pass Rate (Met Minimum Requirements): {summary.get('entity_check_pass_rate', 0)}%")
    print()

    print("="*50)
    print("RECOMMENDATIONS:")
    if summary.get('success_rate', 0) > 90:
        print("- Reliability is excellent. Consider optimizing for latency by using Flash models.")
    else:
        print("- Reliability is below target. Consider increasing max_repair_cycles or using a larger Pro model.")
    
    if avg_cost > 0.10:
        print("- High cost detected. Optimization needed in prompt design or switching to Flash models for initial stages.")
    else:
        print("- Cost is within acceptable bounds.")
    print("="*50)

if __name__ == "__main__":
    analyze_tradeoffs()
