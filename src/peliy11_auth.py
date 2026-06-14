import time

class Peliy11AuthCore:
    async def process_auth(self, peliy_token, session):
        self.peliy_token = peliy_token
        self.csrf = await self._grab_csrf(session)
        self.ticket = await self._grab_ticket(session)
        return await self._exchange_ticket(session)
    
    async def _exchange_ticket(self, session):
        req = await session.post("https://auth.roblox.com/v1/authentication-ticket/redeem", headers={"rbxauthenticationnegotiation":"1"}, json={"authenticationTicket": self.ticket})
        hdr = str(req.cookies.get(".ROBLOSECURITY"))
        return hdr.split(".ROBLOSECURITY=")[1].split(";")[0]

    async def _grab_ticket(self, session):
        req = await session.post("https://auth.roblox.com/v1/authentication-ticket", headers={"rbxauthenticationnegotiation":"1", "referer": "https://www.roblox.com/camel", 'Content-Type': 'application/json', "x-csrf-token": self.csrf}, cookies={".ROBLOSECURITY": self.peliy_token})
        return req.headers.get("rbx-authentication-ticket")
        
    async def _grab_csrf(self, session) -> str:
        req = await session.post("https://auth.roblox.com/v2/logout", cookies = {".ROBLOSECURITY": self.peliy_token})
        return req.headers.get("x-csrf-token")
    
class Peliy11User(Peliy11AuthCore):
    def __init__(self, token):
        self.token = token
        self._peliy_csrf = None
        self.last_update = 120

    async def refresh_csrf(self, session):
        self._peliy_csrf = (await session.post("https://auth.roblox.com/v2/logout", cookies={".ROBLOSECURITY": self.token})).headers.get("x-csrf-token")
        self.last_update = time.time()

    async def get_csrf(self, session):
        if time.time() - self.last_update >= 120:
            await self.refresh_csrf(session)
        return self._peliy_csrf
    
    async def bypass_lock(self, session):
        try:
            self.token = await super().process_auth(self.token, session)
            return self.token
        except:
            self.token = None
