import asyncio
import logging
from app.pipeline.orchestrator import CompilerOrchestrator
from app.config import config

logging.basicConfig(level=logging.INFO)

async def main():
    print("Starting pipeline test...")
    o = CompilerOrchestrator(api_keys=config.api_keys, model='gemini-2.5-flash')
    res = await o.compile('create a simple todo app')
    print("Success:", res.success)
    if not res.success:
        print("Errors:", res.errors)

if __name__ == "__main__":
    asyncio.run(main())
