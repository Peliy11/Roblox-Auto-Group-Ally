from src import peliy11_lock, peliy11_auth, peliy11_sender
import asyncio
import aiohttp
import json

async def peliy11_main():
    with open("config.json", "r", encoding="utf-8") as f:
        conf = json.load(f)
        
    raw_tokens = conf.get("cookies", [])
    if not raw_tokens:
        return
        
    users = []
    unlocks = []
    
    async with aiohttp.ClientSession() as sess:
        for t in raw_tokens:
            u = peliy11_auth.Peliy11User(t)
            users.append(u)
            if conf.get("region_unlock_cookies"):
                unlocks.append(u.bypass_lock(sess))
                
        if unlocks:
            await peliy11_lock.peliy11_gather(conf.get("total_threads", 10), *unlocks)
            
        await peliy11_sender.run_peliy11(sess, users, conf.get("group_id"), conf.get("total_threads", 10))

if __name__ == "__main__":
    asyncio.run(peliy11_main())
