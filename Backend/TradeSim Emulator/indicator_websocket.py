from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Set
import asyncio
import json
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass
from collections import deque
import logging
import sys
from pydantic import BaseModel
from indicator_utils import calculate_rsi, calculate_correlation, get_tick_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('indicator_websocket.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://localhost:5001", "http://localhost:5002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@dataclass
class IndicatorData:
    timestamp: float
    correlation: float
    rsi1: float
    rsi2: float
    pair1: str
    pair2: str

class StrategyParameters(BaseModel):
    id: int
    name: str
    currencyPairs: List[str]
    lotSize: List[str]
    timeFrame: int
    magicNumber: str
    tradeComment: str
    rsiPeriod: int
    correlationWindow: int
    rsiOverbought: float
    rsiOversold: float
    entryThreshold: float
    exitThreshold: float
    startingBalance: float
    status: str

    @property
    def strategy_id(self) -> str:
        return str(self.id)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.calculation_tasks: Dict[str, asyncio.Task] = {}
        self.calculation_running: Dict[str, bool] = {}
        self._lock = asyncio.Lock()
        self.mt5_initialized = False
        self.reconnect_attempts = 0
        self.MAX_RECONNECT_ATTEMPTS = 3
        self.tick_data_cache = {}
        self.last_tick_update = {}
        self.TICK_CACHE_DURATION = 1  # Cache duration in seconds

    async def ensure_mt5_connection(self) -> bool:
        """Ensure MT5 connection is active"""
        try:
            if not self.mt5_initialized:
                logger.info("Initializing MT5...")
                self.mt5_initialized = mt5.initialize()
                if not self.mt5_initialized:
                    logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False
                logger.info("MT5 initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error ensuring MT5 connection: {e}")
            return False

    async def connect(self, websocket: WebSocket, strategy_id: str):
        """Connect with retry mechanism"""
        try:
            if not await self.ensure_mt5_connection():
                logger.error("Cannot accept WebSocket connection - MT5 not initialized")
                await websocket.close(code=1001)
                return

            await websocket.accept()
            async with self._lock:
                if strategy_id not in self.active_connections:
                    self.active_connections[strategy_id] = []
                self.active_connections[strategy_id].append(websocket)
                logger.info(f"WebSocket connection accepted for strategy {strategy_id}")
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            try:
                await websocket.close(code=1001)
            except:
                pass

    def disconnect(self, websocket: WebSocket, strategy_id: str):
        if strategy_id in self.active_connections:
            self.active_connections[strategy_id].remove(websocket)
            if not self.active_connections[strategy_id]:
                self.stop_calculation(strategy_id)
                self.active_connections.pop(strategy_id)
                self.calculation_running[strategy_id] = False
        logger.info(f"WebSocket disconnected for strategy {strategy_id}")

    async def broadcast(self, message: dict, strategy_id: str):
        if strategy_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[strategy_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                self.active_connections[strategy_id].remove(dead)

    def start_calculation(self, strategy_id: str, params: StrategyParameters):
        if strategy_id not in self.calculation_tasks or self.calculation_tasks[strategy_id].done():
            self.calculation_running[strategy_id] = True
            task = asyncio.create_task(self.calculate_indicators(strategy_id, params))
            self.calculation_tasks[strategy_id] = task
            logger.info(f"Started indicator calculation for strategy {strategy_id}")

    def stop_calculation(self, strategy_id: str):
        if strategy_id in self.calculation_tasks:
            self.calculation_running[strategy_id] = False
            if not self.calculation_tasks[strategy_id].done():
                self.calculation_tasks[strategy_id].cancel()
            self.calculation_tasks.pop(strategy_id)
            logger.info(f"Stopped indicator calculation for strategy {strategy_id}")

    async def get_tick_data(self, symbol: str, max_retries: int = 3) -> Optional[Dict]:
        """Get tick data with caching and improved error handling"""
        try:
            current_time = datetime.now()
            
            # Check cache first
            if symbol in self.tick_data_cache:
                last_update = self.last_tick_update.get(symbol)
                if (last_update and 
                    (current_time - last_update).total_seconds() < self.TICK_CACHE_DURATION):
                    return self.tick_data_cache[symbol]

            # Ensure MT5 connection before getting ticks
            if not await self.ensure_mt5_connection():
                logger.error("MT5 not initialized during tick data retrieval")
                return None

            for attempt in range(max_retries):
                try:
                    # Get symbol info first to validate symbol
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is None:
                        logger.error(f"Symbol {symbol} not found")
                        return None

                    # Try to get the latest tick first
                    latest_tick = mt5.symbol_info_tick(symbol)
                    if latest_tick:
                        result = {
                            "bid": float(latest_tick.bid),
                            "ask": float(latest_tick.ask),
                            "time": datetime.fromtimestamp(latest_tick.time),
                            "volume": float(latest_tick.volume)
                        }
                        
                        # Update cache
                        self.tick_data_cache[symbol] = result
                        self.last_tick_update[symbol] = current_time
                        
                        return result

                    # Fallback to copy_ticks_from if symbol_info_tick fails
                    ticks = mt5.copy_ticks_from(
                        symbol,
                        current_time - timedelta(seconds=5),
                        100,
                        mt5.COPY_TICKS_ALL
                    )

                    if ticks is not None and len(ticks) > 0:
                        last_tick = ticks[-1]
                        result = {
                            "bid": float(last_tick[1]),
                            "ask": float(last_tick[2]),
                            "time": datetime.fromtimestamp(last_tick[5] / 1000),
                            "volume": float(last_tick[4])
                        }
                        
                        # Update cache
                        self.tick_data_cache[symbol] = result
                        self.last_tick_update[symbol] = current_time
                        
                        return result

                    logger.warning(f"No ticks received for {symbol} on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.1)  # Shorter delay between retries
                        continue

                except Exception as e:
                    logger.error(f"Error getting tick data for {symbol} (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.1)
                        continue

            # If all attempts failed, try to use cached data if not too old
            if symbol in self.tick_data_cache:
                last_update = self.last_tick_update.get(symbol)
                if last_update and (current_time - last_update).total_seconds() < 5:
                    logger.warning(f"Using cached tick data for {symbol}")
                    return self.tick_data_cache[symbol]

            logger.error(f"Failed to get tick data for {symbol} after {max_retries} attempts")
            return None

        except Exception as e:
            logger.error(f"Unexpected error getting tick data for {symbol}: {e}")
            return None

    async def calculate_indicators(self, strategy_id: str, params: StrategyParameters):
        """Calculate indicators with improved error handling and tick data management"""
        try:
            logger.info(f"Starting calculation loop for strategy {strategy_id}")
            
            pair1, pair2 = params.currencyPairs
            error_count = 0
            MAX_ERRORS = 5
            last_successful_data = None

            while self.calculation_running.get(strategy_id, False):
                try:
                    if not await self.ensure_mt5_connection():
                        logger.error("MT5 connection lost during calculation")
                        error_count += 1
                        if error_count >= MAX_ERRORS:
                            logger.error("Max errors reached, stopping calculation")
                            break
                        await asyncio.sleep(1)
                        continue

                    # Get tick data for both pairs
                    tick_data = {}
                    tick_data_success = True
                    for pair in [pair1, pair2]:
                        data = await self.get_tick_data(pair)
                        if data:
                            tick_data[pair] = data
                        else:
                            tick_data_success = False
                            logger.warning(f"No tick data for {pair}")
                            break

                    if not tick_data_success:
                        if last_successful_data:
                            logger.warning("Using last successful data")
                            tick_data = last_successful_data
                        else:
                            error_count += 1
                            if error_count >= MAX_ERRORS:
                                logger.error("Max errors reached, stopping calculation")
                                break
                            await asyncio.sleep(1)
                            continue

                    # Calculate indicators
                    correlation = calculate_correlation(
                        pair1, pair2, 
                        params.correlationWindow, 
                        params.timeFrame
                    )

                    rsi_values = {
                        pair1: calculate_rsi(pair1, params.rsiPeriod, params.timeFrame),
                        pair2: calculate_rsi(pair2, params.rsiPeriod, params.timeFrame)
                    }

                    # Store successful data
                    if tick_data_success:
                        last_successful_data = tick_data.copy()
                        error_count = 0  # Reset error count on success

                    # Prepare and send data
                    indicator_data = {
                        "timestamp": datetime.now().isoformat(),
                        "correlation": correlation if correlation is not None else "N/A",
                        "rsi_values": {
                            pair1: rsi_values[pair1] if rsi_values[pair1] is not None else "N/A",
                            pair2: rsi_values[pair2] if rsi_values[pair2] is not None else "N/A"
                        },
                        "current_prices": {
                            pair1: tick_data[pair1]["bid"],
                            pair2: tick_data[pair2]["bid"]
                        },
                        "thresholds": {
                            "entry": params.entryThreshold,
                            "exit": params.exitThreshold,
                            "rsi_overbought": params.rsiOverbought,
                            "rsi_oversold": params.rsiOversold
                        }
                    }

                    await self.broadcast(indicator_data, strategy_id)
                    
                except Exception as e:
                    logger.error(f"Error in calculation loop: {e}")
                    error_count += 1
                    if error_count >= MAX_ERRORS:
                        logger.error("Max errors reached, stopping calculation")
                        break
                
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(f"Calculation cancelled for strategy {strategy_id}")
        except Exception as e:
            logger.error(f"Fatal error in calculate_indicators: {e}")
        finally:
            self.calculation_running[strategy_id] = False

manager = ConnectionManager()

@app.post("/start-stream/")
async def start_stream(params: StrategyParameters):
    """Start indicator calculation"""
    try:
        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize MT5")

        # Start calculation task - no need to save state
        manager.start_calculation(params.strategy_id, params)

        return {
            "status": "success",
            "message": "Indicator stream started",
            "websocket_url": f"ws://localhost:5002/ws/{params.strategy_id}"
        }

    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{strategy_id}")
async def websocket_endpoint(websocket: WebSocket, strategy_id: str):
    """WebSocket endpoint for streaming indicator data"""
    try:
        await manager.connect(websocket, strategy_id)
        
        try:
            while True:
                # Keep connection alive and handle client messages if needed
                data = await websocket.receive_text()
                logger.debug(f"Received message from client: {data}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            manager.disconnect(websocket, strategy_id)
            
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
        try:
            await websocket.close(code=1000)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting indicator WebSocket server")
    uvicorn.run(app, host="0.0.0.0", port=5002) 