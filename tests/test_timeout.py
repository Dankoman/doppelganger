
import asyncio
from camoufox.async_api import AsyncCamoufox

async def test():
    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        url = "https://www.pornpics.com/pornstars/marta-e/"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print("Successfully loaded!")
            title = await page.title()
            print(f"Title: {title}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
