import logging
import json
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Assuming AppState and AppSettings are importable.
# If direct import causes issues (e.g. circular), type hints might be an option
# or passing specific dependencies to job functions.
from src.app_state import AppState
from src.config import AppSettings
from src.trading_strategies import execute_strategy_loop # For the strategy execution job
from src.core.utils import broadcast_websocket_message # For broadcasting elite recommendations
from src.market_data_handling import _sync_truedata_globals_to_app_state # For TrueData global state sync

logger = logging.getLogger(__name__)

async def run_system_health_check_job(app_state: AppState, settings: AppSettings):
    """
    Periodically checks system health, database, and Redis connectivity.
    Updates app_state.system_status.system_health.
    """
    logger.info("Scheduler: Running system health check job...")
    health_issues = []

    # Check DB Connection (example: try a simple query)
    if app_state.clients.db_pool:
        try:
            # Assuming a simple query; specific to DB type if not using an ORM
            # For SQLite (path as pool):
            if isinstance(app_state.clients.db_pool, str):
                import aiosqlite
                async with aiosqlite.connect(app_state.clients.db_pool) as db:
                    await db.execute("SELECT 1")
            else: # Assuming asyncpg pool
                 async with app_state.clients.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            app_state.system_status.database_connected = True
            logger.debug("HealthCheck: Database connection OK.")
        except Exception as e:
            app_state.system_status.database_connected = False
            health_issues.append(f"DB_ERROR: {str(e)[:50]}")
            logger.error(f"HealthCheck: Database connection failed: {e}", exc_info=True)
    else:
        app_state.system_status.database_connected = False
        health_issues.append("DB_NO_POOL")
        logger.warning("HealthCheck: Database pool not available.")

    # Check Redis Connection
    if app_state.clients.redis_client:
        try:
            await app_state.clients.redis_client.ping()
            app_state.system_status.redis_connected = True
            logger.debug("HealthCheck: Redis connection OK.")
        except Exception as e:
            app_state.system_status.redis_connected = False
            health_issues.append(f"REDIS_ERROR: {str(e)[:50]}")
            logger.error(f"HealthCheck: Redis connection failed: {e}", exc_info=True)
    else:
        app_state.system_status.redis_connected = False
        # Not necessarily an issue if Redis is optional
        logger.info("HealthCheck: Redis client not available (may be optional).")


    # Update overall system health
    if not health_issues:
        app_state.system_status.system_health = "OPERATIONAL"
    else:
        app_state.system_status.system_health = f"DEGRADED: {', '.join(health_issues)}"

    app_state.system_status.last_system_update_utc = datetime.utcnow()
    logger.info(f"Scheduler: System health check complete. Status: {app_state.system_status.system_health}")

async def run_scan_elite_recommendations_job(app_state: AppState, settings: AppSettings):
    """
    Periodically scans for elite recommendations using the EliteEngine.
    Stores new recommendations and broadcasts them.
    """
    logger.info("Scheduler: Running scan for elite recommendations job...")
    if not app_state.clients.elite_engine:
        logger.warning("EliteEngine not available. Skipping elite recommendations scan.")
        return

    try:
        # Assuming elite_engine has a method like scan_and_store_recommendations
        # that returns new recommendations suitable for broadcasting.
        # This method would internally handle DB storage.
        new_recommendations = []
        if hasattr(app_state.clients.elite_engine, 'scan_for_elite_trades') and \
           callable(getattr(app_state.clients.elite_engine, 'scan_for_elite_trades')):

            # The scan_for_elite_trades in the original file seems to directly store them.
            # Let's assume it returns a list of what it found or stored for broadcasting.
            # If it doesn't, this job might need to query DB after scan.
            recs_data_from_scan = await app_state.clients.elite_engine.scan_for_elite_trades(
                app_state=app_state, settings=settings
            )
            # Assuming recs_data_from_scan is a list of dicts ready for broadcast
            if recs_data_from_scan and isinstance(recs_data_from_scan, list):
                 new_recommendations = recs_data_from_scan # Use directly if format matches
            elif recs_data_from_scan: # If it's a count or other status
                 logger.info(f"Elite scan completed, returned: {recs_data_from_scan}. Querying DB for new recs if needed.")
                 # Potentially query DB here if scan_for_elite_trades doesn't return them directly.
                 # For now, assume it might return the list of recommendations.

        if new_recommendations:
            logger.info(f"Found {len(new_recommendations)} new elite recommendations. Broadcasting...")
            broadcast_message = {
                "type": "elite_recommendations_update",
                "data": new_recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
            await broadcast_websocket_message(app_state.system_status.websocket_connections_set, broadcast_message)
            logger.info(f"{len(new_recommendations)} elite recommendations broadcasted.")
        else:
            logger.info("No new elite recommendations found in this scan.")

    except Exception as e:
        logger.error(f"Error during elite recommendations scan: {e}", exc_info=True)

async def run_execute_strategy_loop_job(app_state: AppState, settings: AppSettings):
    """
    Periodically executes the main trading strategy loop.
    """
    logger.debug("Scheduler: Running execute strategy loop job...")
    try:
        await execute_strategy_loop(app_state, settings)
        logger.debug("Scheduler: Strategy loop execution finished.")
    except Exception as e:
        logger.error(f"Error during scheduled strategy loop execution: {e}", exc_info=True)


def initialize_scheduler(app_state: AppState, settings: AppSettings) -> AsyncIOScheduler:
    """
    Creates, configures, and returns the APScheduler instance.
    """
    logger.info(f"Initializing APScheduler with timezone: {settings.TIMEZONE}")
    scheduler = AsyncIOScheduler(timezone=str(settings.TIMEZONE))

    # Add system health check job
    scheduler.add_job(
        run_system_health_check_job,
        trigger=IntervalTrigger(seconds=settings.HEALTH_CHECK_INTERVAL_SECONDS),
        kwargs={'app_state': app_state, 'settings': settings},
        id='system_health_check',
        name='System Health Check',
        replace_existing=True
    )
    logger.info(f"Added 'system_health_check' job. Interval: {settings.HEALTH_CHECK_INTERVAL_SECONDS}s")

    # Add elite recommendations scan job
    if app_state.clients.elite_engine: # Only add if engine is available
        scheduler.add_job(
            run_scan_elite_recommendations_job,
            trigger=IntervalTrigger(seconds=settings.ELITE_SCAN_INTERVAL_SECONDS),
            kwargs={'app_state': app_state, 'settings': settings},
            id='scan_elite_recommendations',
            name='Scan Elite Recommendations',
            replace_existing=True
        )
        logger.info(f"Added 'scan_elite_recommendations' job. Interval: {settings.ELITE_SCAN_INTERVAL_SECONDS}s")
    else:
        logger.warning("EliteEngine not found in app_state.clients. 'scan_elite_recommendations' job NOT added.")

    # Add trading strategy execution loop job
    scheduler.add_job(
        run_execute_strategy_loop_job,
        trigger=IntervalTrigger(seconds=settings.STRATEGY_LOOP_INTERVAL_SECONDS),
        kwargs={'app_state': app_state, 'settings': settings},
        id='execute_strategy_loop',
        name='Execute Trading Strategy Loop',
        replace_existing=True
    )
    logger.info(f"Added 'execute_strategy_loop' job. Interval: {settings.STRATEGY_LOOP_INTERVAL_SECONDS}s")

    # Add TrueData global state sync job
    # Ensure TRUEDATA_STATE_SYNC_INTERVAL_SECONDS is in AppSettings
    if hasattr(settings, 'TRUEDATA_STATE_SYNC_INTERVAL_SECONDS'):
        scheduler.add_job(
            _sync_truedata_globals_to_app_state,
            trigger=IntervalTrigger(seconds=settings.TRUEDATA_STATE_SYNC_INTERVAL_SECONDS),
            kwargs={'app_state': app_state}, # Only needs app_state
            id='sync_truedata_globals',
            name='Sync TrueData Globals to AppState',
            replace_existing=True
        )
        logger.info(f"Added '_sync_truedata_globals_to_app_state' job. Interval: {settings.TRUEDATA_STATE_SYNC_INTERVAL_SECONDS}s")
    else:
        logger.warning("'TRUEDATA_STATE_SYNC_INTERVAL_SECONDS' not found in settings. TrueData global sync job NOT added.")

    logger.info("APScheduler initialization complete with jobs.")
    return scheduler

```
