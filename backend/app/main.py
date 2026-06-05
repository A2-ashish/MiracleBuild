from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import logging
import asyncio

from app.config import config
from app.pipeline.orchestrator import CompilerOrchestrator

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="Miracle Build API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    prompt: str

@app.get("/api/compile/stream")
async def compile_app_stream(prompt: str, model: str = None, request: Request = None):
    """
    Endpoint to trigger the compiler pipeline.
    Uses Server-Sent Events (SSE) to stream progress via GET request (for EventSource).
    """
    async def sse_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def stage_callback(stage_name: str, status: str, data: dict):
            """Regular async function that pushes events into the queue."""
            event_data = {
                "type": "stage_update",
                "stage": stage_name,
                "status": status,
                "duration_ms": data.get("duration_ms"),
                "tokens": data.get("tokens"),
            }
            await queue.put(event_data)

        # Setup the orchestrator
        orchestrator = CompilerOrchestrator(
            api_keys=config.api_keys,
            model=model or config.DEFAULT_MODEL,
            max_repair_cycles=config.MAX_REPAIR_CYCLES,
        )

        async def run_pipeline():
            try:
                result = await orchestrator.compile(prompt, callback=stage_callback)
                await queue.put({"type": "complete", "status": "success", "result": result.model_dump()})
            except Exception as e:
                logger.exception("Compilation failed")
                await queue.put({"type": "error", "message": str(e)})
            finally:
                await queue.put(None)  # Sentinel to stop the generator

        # Start the pipeline in the background
        task = asyncio.create_task(run_pipeline())

        # Send init event
        yield f"data: {json.dumps({'type': 'init', 'status': 'connected'})}\n\n"

        # Drain the queue and yield SSE events until sentinel
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

        await task  # Ensure the task is fully done

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/api/compile")
async def compile_app(req: CompileRequest, request: Request):
    """Fallback standard POST endpoint for compilation."""
    orchestrator = CompilerOrchestrator(
        api_keys=config.api_keys,
        model=config.DEFAULT_MODEL,
        max_repair_cycles=config.MAX_REPAIR_CYCLES,
    )
    result = await orchestrator.compile(req.prompt)
    if not result.success:
        return JSONResponse(status_code=400, content=result.model_dump())
    return result.model_dump()

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
