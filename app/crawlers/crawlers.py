import sys
import asyncio
import aioschedule
from app.core.config import settings
from app.crawlers.data_handlers.get_data_from_db import get_data_from_db
from app.crawlers.smm_engines.smm_engines import SmmEngine
from app.logging.notify import notify


async def scheduler(smm_engine):
    aioschedule.every(1).seconds.do(get_data_from_db, smm_engine)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(settings.REPEAT_TASKS_SECONDS)

if __name__ == "__main__":
    try:
        smm_engine = SmmEngine[sys.argv[1]]
    except (KeyError, IndexError):
        notify.error("Invalid SmmEngine. Exiting...")
        sys.exit()
    asyncio.run(scheduler(smm_engine))
