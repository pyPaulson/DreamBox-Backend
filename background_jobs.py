"""
Background job runner for auto-save processing
Run this script as a separate process to handle auto-save executions
"""

import asyncio
import logging
import signal
import sys
from app.services.auto_save_scheduler import auto_save_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_save_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping auto-save scheduler...")
    auto_save_scheduler.stop()
    sys.exit(0)


async def main():
    """Main function to run the auto-save scheduler"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting auto-save background job runner...")
    
    try:
        await auto_save_scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in auto-save scheduler: {str(e)}")
    finally:
        auto_save_scheduler.stop()
        logger.info("Auto-save scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())
