import asyncio
import platform
import random
import traceback

import aiohttp

from core import Grass
from core.autoreger import AutoReger
from core.utils import logger
from core.utils.exception import LowProxyScoreException, ProxyScoreNotFoundException, ProxyForbiddenException
from core.utils.generate.person import Person
from data.config import ACCOUNTS_FILE_PATH, PROXIES_FILE_PATH, REGISTER_ACCOUNT_ONLY, THREADS
from core.utils.global_store import mined_grass_counts, lock


async def log_total_mined_grass_every_minute():
    while True:
        await asyncio.sleep(120)  # Menunggu selama 1 menit
        async with lock:
            total_mined = sum(mined_grass_counts.values())
        logger.opt(colors=True).info(f"<yellow>Total Mined Grass: {total_mined}</yellow>.")
        
        

#
async def worker_task(_id, account: str):
    consumables = account.split(":")[:2]

    if len(consumables) == 1:
        email = consumables[0]
        password = Person().random_string(8)
    else:
        email, password = consumables

    await asyncio.sleep(random.uniform(1, 1.5) * _id)
    logger.info(f"Starting №{_id} | {email} | {password}")

    grass = None
    try:
        grass = Grass(_id, email, password)

        if REGISTER_ACCOUNT_ONLY:
            await grass.create_account()
        else:
            await grass.start()

    except aiohttp.ClientError as e:
        log_msg = str(e) if "</html>" not in str(e) else "Html page response, 504"
        logger.error(f"{_id} | Server not responding | Error: {log_msg}")
        await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"{_id} | not handled exception | error: {e} {traceback.format_exc()}")
    finally:
        if grass:
            await grass.session.close()

async def main():
    autoreger = AutoReger.get_accounts(
        ACCOUNTS_FILE_PATH, PROXIES_FILE_PATH,
        with_id=True
    )

    accounts = autoreger.accounts  # Gunakan semua akun yang tersedia

    if REGISTER_ACCOUNT_ONLY:
        msg = "Register account only mode!"
    else:
        msg = "Mining mode ON"

    threads = len(accounts)  # Gunakan jumlah akun sebagai jumlah thread
    logger.info(f"Threads: {threads} | {msg}")
    asyncio.create_task(log_total_mined_grass_every_minute())

    tasks = [worker_task(i, accounts[i % len(accounts)]) for i in range(threads)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
