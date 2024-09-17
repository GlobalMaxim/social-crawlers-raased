import sys
import asyncio
import aioschedule
from app.core.config import settings
from app.crawlers.data_handlers.get_data_for_frofile_crawlers import get_data_from_db
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.logging.notify import notify


async def scheduler():
    aioschedule.every(1).seconds.do(get_data_from_db)

    while True:
        await aioschedule.run_pending()
        # await asyncio.sleep(settings.REPEAT_TASKS_SECONDS)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(scheduler())
