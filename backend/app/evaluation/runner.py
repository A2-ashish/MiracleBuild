"""CLI runner for the evaluation suite."""
import asyncio
import json
import logging
import argparse
from pathlib import Path

from app.config import config
from app.pipeline.orchestrator import CompilerOrchestrator
from app.evaluation.metrics import MetricsCollector

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def run_evaluations(limit: int = None, output: str = "eval_results.json"):
    prompts_file = Path(__file__).parent / "test_prompts.json"
    if not prompts_file.exists():
        logger.error(f"Prompts file not found at {prompts_file}")
        return

    with open(prompts_file, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    if limit:
        prompts = prompts[:limit]

    logger.info(f"Starting evaluation of {len(prompts)} prompts...")
    
    collector = MetricsCollector()
    orchestrator = CompilerOrchestrator(
        api_keys=config.api_keys,
        model=config.DEFAULT_MODEL,
        max_repair_cycles=config.MAX_REPAIR_CYCLES,
    )

    for i, test in enumerate(prompts, 1):
        logger.info(f"[{i}/{len(prompts)}] Testing: {test['id']} - {test['description']}")
        try:
            result = await orchestrator.compile(test["prompt"])
            collector.add_result(
                prompt_id=test["id"],
                prompt_text=test["prompt"],
                category=test["category"],
                expected_entities_min=test.get("expected_entities_min", 0),
                compilation=result
            )
            if result.success:
                logger.info(f"  -> SUCCESS in {result.metrics.total_duration_ms:.0f}ms")
            else:
                logger.warning(f"  -> FAILED: {', '.join(result.errors)}")
        except Exception as e:
            logger.exception(f"  -> UNEXPECTED ERROR: {e}")

    summary = collector.get_summary()
    details = collector.get_per_prompt_results()

    output_data = {
        "summary": summary,
        "details": details
    }
    
    with open(output, "w") as f:
        json.dump(output_data, f, indent=2)
        
    logger.info("Evaluation complete!")
    logger.info(json.dumps(summary, indent=2))
    logger.info(f"Results saved to {output}")

def main():
    parser = argparse.ArgumentParser(description="Run Miracle Build Evaluation Suite")
    parser.add_argument("--limit", type=int, help="Limit number of prompts to run")
    parser.add_argument("--output", type=str, default="eval_results.json", help="Output JSON file")
    
    args = parser.parse_args()
    asyncio.run(run_evaluations(limit=args.limit, output=args.output))

if __name__ == "__main__":
    main()
