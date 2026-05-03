import asyncio
from camoufox.async_api import AsyncCamoufox

async def setup_resource_blocking(context):
    async def handle_route(route):
        req = route.request
        if any(x in req.url for x in [
            "google-analytics", "doubleclick", "googletagmanager", "yandex.ru", 
            "adnxs", "popads", "onclickads", "tsyndicate.com", "realsrv.com",
            "trafficstars.com", "exoclick.com", "juicyads.com"
        ]):
            return await route.abort()
        await route.continue_()
    
    await context.route("**/*", handle_route)

async def main():
    async with AsyncCamoufox(headless=True) as browser:
        async with await browser.new_context() as context:
            await setup_resource_blocking(context)
            page = await context.new_page()
            print("Goto start")
            try:
                await page.goto("https://www.pornpics.com/pornstars/miko-dai/", wait_until="commit", timeout=15000)
                print("Goto success")
            except Exception as e:
                print("Goto failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
