import random, asyncio
from . import peliy11_lock

class Peliy11Engine:
    @staticmethod
    async def fetch_assets(session, user):
        req = await session.get("https://catalog.roblox.com/v1/search/items?category=Clothing&limit=120&salesTypeFilter=1&sortType=3&subcategory=ClassicShirts", 
                            cookies={".ROBLOSECURITY": user.token}, 
                            headers={"x-csrf-token": await user.get_csrf(session)})
        if req.status != 200:
            if req.status == 429:
                await user.refresh_csrf(session)
            return []
        data = await req.json()
        return [itm['id'] for itm in data.get("data", [])]
    
    @staticmethod
    async def extract_groups(session, user, gid, visited):
        req = await session.get(f"https://groups.roblox.com/v1/groups/{gid}/relationships/allies?maxRows=100&sortOrder=Asc&startRowIndex=0",
                                cookies={".ROBLOSECURITY": user.token},
                                headers={"x-csrf-token": await user.get_csrf(session)})
        if req.status != 200:
            if req.status == 429:
                await user.refresh_csrf(session)
            return []
        data = await req.json()
        found = []
        for grp in data.get("relatedGroups", []):
            if grp["id"] not in visited:
                with open("src/data/allied.txt", "a") as f:
                    f.write(f"\n{grp['id']}")
                found.append(grp["id"])
        return found

    @staticmethod
    async def process_assets(session, user, visited, a_ids):
        req = await session.post("https://catalog.roblox.com/v1/catalog/items/details", 
                                json={"items": [{"itemType": "Asset", "id": aid} for aid in a_ids]},
                                cookies={".ROBLOSECURITY": user.token},
                                headers={"x-csrf-token": await user.get_csrf(session)})
        if req.status != 200:
            if req.status == 429:
                await user.refresh_csrf(session)
            return []
        data = await req.json()
        found = []
        for itm in data.get("data", []):
            if itm.get("creatorType") == "Group":
                tid = itm.get("creatorTargetId")
                if tid not in visited:
                    visited.append(tid)
                    with open("src/data/allied.txt", "a") as f:
                        f.write(f"\n{tid}")
                    found.append(tid)
        return found
    
    @staticmethod
    async def dispatch_request(session, user, target, main_group):
        req = await session.post(f"https://groups.roblox.com/v1/groups/{main_group}/relationships/allies/{target}",
                                cookies={".ROBLOSECURITY": user.token}, 
                                headers={"x-csrf-token": await user.get_csrf(session)})
        if req.status == 200:
            print(f"Peliy11 [+] Success -> {target}")
        else:
            if req.status == 429:
                await user.refresh_csrf(session)
            print(f"Peliy11 [-] Failed -> {target}")

async def peliy11_task(session, user, target, main_group, visited):
    try:
        await Peliy11Engine.dispatch_request(session, user, target, main_group)
        return await Peliy11Engine.extract_groups(session, user, target, visited)
    except:
        return []
    
async def run_peliy11(session, accounts, main_group, limit):
    try:
        with open("src/data/allied.txt", "r") as f:
            visited = f.read().splitlines()
    except FileNotFoundError:
        visited = []
        
    queue = []
    while True:
        try:
            usr = random.choice(accounts)
            assets = await Peliy11Engine.fetch_assets(session, usr)
            targets = await Peliy11Engine.process_assets(session, usr, visited, assets)
            
            for t in targets:
                if t not in visited:
                    visited.append(t)
                queue.append(t)
                
            while queue:
                try:
                    jobs = []
                    idx = 0
                    for t in list(queue):
                        if idx >= len(accounts):
                            idx = 0
                            break
                        jobs.append(peliy11_task(session, accounts[idx], t, main_group, visited))
                        queue.remove(t)
                        idx += 1
                        
                    res = await peliy11_lock.peliy11_gather(limit, *jobs)
                    for groups in res:
                        if groups:
                            for g in groups:
                                if g not in queue and g not in visited:
                                    queue.append(g)
                    await asyncio.sleep(60 / max(1, len(accounts)))
                except:
                    continue
        except:
            pass
