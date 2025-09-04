"""
Voice Assistant - Refactored Structure
======================================
continuing your work on separating components into logical files
keeping everything in single directory for simplicity
focus on reducing cognitive load through clear interfaces
"""

# ==========================
# main.py (updated)
# ==========================
"""
main.py - entry point for voice assistant
minimal code here - just starts the system
"""

import asyncio
import logging
from tree_logger import setup_logging
from system_controller import SystemController
from debug_monitor import DebugMonitor

#MARK: setup logging
# log = setup_logging(log_per_session=False)
# logger = logging.getLogger(__name__)

#MARK: setup logging 
# make sure to call this before any other logger usage
logger = setup_logging(
    config_file="tree_logger_config.json",
    logger_name="treelogger",
    log_per_session=True
)


#MARK: main
async def main():
    """start the voice assistant"""
    logger.info("starting voice assistant")
    
    # create system controller
    controller = SystemController()
    
    # create debug monitor
    monitor = DebugMonitor(controller.bus)
    
    # run the system
    try:
        await controller.run()
    except Exception as e:
        logger.error(f"system error: {e}")
        raise
    finally:
        logger.info("voice assistant stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted by user")