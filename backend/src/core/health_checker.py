import logging
import psutil
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from ..core.config import Settings

class HealthChecker:
    def __init__(self, config: Settings):
        self.config = config
        self.logger = logging.getLogger("health_checker")
        self._start_time = datetime.now()
        self._is_running = False
        self._check_interval = 30  # seconds
        self._last_check = None
        self._health_status = {
            "status": "unknown",
            "last_check": None,
            "uptime": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }

    async def start(self):
        """Start the health checker background task."""
        if not self._is_running:
            self._is_running = True
            asyncio.create_task(self._background_check())
            self.logger.info("Health checker started")

    async def stop(self):
        """Stop the health checker."""
        self._is_running = False
        self.logger.info("Health checker stopped")

    async def _background_check(self):
        """Background task to periodically check system health."""
        while self._is_running:
            try:
                await self.check_health()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                self.logger.error(f"Error in health check: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    async def check_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent()
            
            self._health_status.update({
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "uptime": (datetime.now() - self._start_time).total_seconds(),
                "memory_usage": memory.percent,
                "cpu_usage": cpu
            })
            
            self._last_check = datetime.now()
            return self._health_status
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            self._health_status["status"] = "unhealthy"
            return self._health_status

    async def check_liveness(self) -> bool:
        """Check if the application is alive."""
        return self._is_running

    async def check_readiness(self) -> bool:
        """Check if the application is ready to serve requests."""
        if not self._last_check:
            return False
        
        # Consider the system ready if the last health check was within the last minute
        return (datetime.now() - self._last_check).total_seconds() < 60

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics."""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "uptime": (datetime.now() - self._start_time).total_seconds()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Get the current health status."""
        return self._health_status 