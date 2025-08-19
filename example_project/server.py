from hango.server import *
from .db import init_db, add_schedule, scheduler_loop
import asyncio
server: Server = app(cache='redis')
from example_project.handler import *
import contextlib


async def main():
    init_db()
    add_schedule("daily_balance", 86400)

    server_task = asyncio.create_task(server.start_server_async())
    scheduler_task = asyncio.create_task(scheduler_loop(send_balance_email))
    try:
        await server_task     
    finally:
        scheduler_task.cancel()      
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler_task    
            
if __name__ == "__main__":
    asyncio.run(main())
