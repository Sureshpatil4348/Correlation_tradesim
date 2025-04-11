from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import MetaTrader5 as mt5
import logging
from indicator_websocket import app as websocket_app

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Add CORS middleware with updated origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Default React port
        "http://localhost:5173",  # Vite React port
        "http://127.0.0.1:5173"   # Alternative Vite local address
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply the same CORS settings to the websocket app
websocket_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the WebSocket app
app.mount("/", websocket_app)

@app.on_event("startup")
async def startup_event():
    """Initialize MT5 connection on startup"""
    try:
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            raise Exception("MT5 initialization failed")
        logger.info("MT5 initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MT5 connection on shutdown"""
    try:
        mt5.shutdown()
        logger.info("MT5 shutdown successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "serve_indicators:app",
        host="0.0.0.0",
        port=5002,
        reload=False,
        log_level="info"
    ) 