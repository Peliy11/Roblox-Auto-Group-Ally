import asyncio

async def peliy11_executor(peliy_sem, peliy_job):
    try:
        async with peliy_sem:
            return await peliy_job
    except Exception:
        pass

async def peliy11_gather(concurrency_limit, *jobs):
    peliy_sem = asyncio.Semaphore(concurrency_limit)
    return await asyncio.gather(*[peliy11_executor(peliy_sem, j) for j in jobs])