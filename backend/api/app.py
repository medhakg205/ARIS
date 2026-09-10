"""
ARIS Main FastAPI Application.
Assembles all REST API endpoints and real-time WebSocket endpoints.
Configures CORS, exception handlers, and event loops.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.telemetry.telemetry_schema import ArisException
from backend.api.error_handlers import (
    aris_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from backend.api.websocket_server import ws_manager
from backend.api.dependencies import get_simulator, get_serial_mgr

# Import all route modules
from backend.api.routes_boards import router as boards_router
from backend.api.routes_connection import router as connection_router
from backend.api.routes_firmware import router as firmware_router
from backend.api.routes_runs import router as runs_router
from backend.api.routes_telemetry import router as telemetry_router
from backend.api.routes_analysis import router as analysis_router
from backend.api.routes_optimization import router as optimization_router
from backend.api.routes_experiments import router as experiments_router
from backend.api.routes_validation import router as validation_router
from backend.api.routes_ai import router as ai_router
from backend.api.routes_health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager configuring the asyncio event loop for WebSockets."""
    loop = asyncio.get_running_loop()
    ws_manager.set_loop(loop)
    yield
    # Shutdown cleanup
    get_simulator().stop()
    get_serial_mgr().disconnect()


# Initialize FastAPI Application
app = FastAPI(
    title="ARIS Analytical & Backend Core",
    description="Adaptive Runtime Intelligence System for Real Arduino Microcontrollers",
    version="1.0.0",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS) for desktop UI and external agents
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Canonical Error Handlers
app.add_exception_handler(ArisException, aris_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount REST Routers
app.include_router(boards_router)
app.include_router(connection_router)
app.include_router(firmware_router)
app.include_router(runs_router)
app.include_router(telemetry_router)
app.include_router(analysis_router)
app.include_router(optimization_router)
app.include_router(experiments_router)
app.include_router(validation_router)
app.include_router(ai_router)
app.include_router(health_router)


# Canonical WebSocket Endpoint: /ws/telemetry/{run_id}
@app.websocket("/ws/telemetry/{run_id}")
async def websocket_telemetry_run(websocket: WebSocket, run_id: str):
    """
    Real-time telemetry stream for a specific run.
    The frontend will depend on this exact path.
    """
    await ws_manager.connect(websocket, run_id=run_id)
    try:
        while True:
            # Keep connection alive; accept optional client control pings
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, run_id=run_id)


# Backward-compatible catch-all WebSocket endpoint: /ws/telemetry
@app.websocket("/ws/telemetry")
async def websocket_telemetry_all(websocket: WebSocket):
    """
    Catch-all real-time telemetry stream for active execution sessions.
    """
    await ws_manager.connect(websocket, run_id=None)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, run_id=None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.app:app", host="127.0.0.1", port=8765, reload=False)
