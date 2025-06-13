"""
Autonomous Trading API
Handles automated trading operations
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import logging
from core.orchestrator import TradingOrchestrator
from models.responses import (
    BaseResponse,
    TradingStatusResponse,
    PositionResponse,
    PerformanceMetricsResponse,
    StrategyResponse,
    RiskMetricsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/autonomous")

# Dependency injection for orchestrator
def get_orchestrator() -> TradingOrchestrator:
    """Get the singleton orchestrator instance"""
    return TradingOrchestrator.get_instance()

@router.get("/status", response_model=TradingStatusResponse)
async def get_status(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get current autonomous trading status"""
    try:
        status = await orchestrator.get_trading_status()
        return TradingStatusResponse(
            success=True,
            message="Trading status retrieved successfully",
            data={
                "is_active": status["is_active"],
                "session_id": status["session_id"],
                "start_time": status["start_time"],
                "last_heartbeat": status["last_heartbeat"],
                "active_strategies": status["active_strategies"],
                "active_positions": status["active_positions"],
                "total_trades": status["total_trades"],
                "daily_pnl": status["daily_pnl"],
                "risk_status": status["risk_status"],
                "market_status": status["market_status"],
                "timestamp": datetime.utcnow()
            }
        )
    except Exception as e:
        logger.error(f"Error getting trading status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start", response_model=BaseResponse)
async def start_trading(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Start autonomous trading"""
    try:
        await orchestrator.enable_trading()
        return BaseResponse(
            success=True,
            message="Autonomous trading started successfully"
        )
    except Exception as e:
        logger.error(f"Error starting trading: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=BaseResponse)
async def stop_trading(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Stop autonomous trading"""
    try:
        await orchestrator.disable_trading()
        return BaseResponse(
            success=True,
            message="Autonomous trading stopped successfully"
        )
    except Exception as e:
        logger.error(f"Error stopping trading: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions", response_model=PositionResponse)
async def get_positions(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get current positions"""
    try:
        positions = await orchestrator.position_tracker.get_all_positions()
        return PositionResponse(
            success=True,
            message="Positions retrieved successfully",
            data=positions
        )
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get trading performance metrics"""
    try:
        metrics = await orchestrator.metrics.get_trading_metrics()
        return PerformanceMetricsResponse(
            success=True,
            message="Performance metrics retrieved successfully",
            data=metrics
        )
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies", response_model=StrategyResponse)
async def get_strategies(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get active trading strategies"""
    try:
        strategies = await orchestrator.strategy_manager.get_active_strategies()
        return StrategyResponse(
            success=True,
            message="Strategies retrieved successfully",
            data=strategies
        )
    except Exception as e:
        logger.error(f"Error getting strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    orchestrator: TradingOrchestrator = Depends(get_orchestrator)
):
    """Get current risk metrics"""
    try:
        risk_metrics = await orchestrator.risk_manager.get_risk_metrics()
        return RiskMetricsResponse(
            success=True,
            message="Risk metrics retrieved successfully",
            data=risk_metrics
        )
    except Exception as e:
        logger.error(f"Error getting risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
