import asyncio
from camoufox.async_api import AsyncCamoufox
from urllib.parse import urljoin

async def test():
    async with AsyncCamoufox(headless=True) as browser:
        async with await browser.new_context() as context:
            page = await context.new_page()
            url = "https://www.pornpics.com/pornstars/shay-jordan/"
            print(f"Loading {url}...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                print("DOMContentLoaded reached.")
            except Exception as e:
                print(f"Goto failed: {e}")
                
            selector = "li.thumbwook a[href*='/galleries/']"
            print(f"Waiting for selector: {selector}")
            try:
                await page.wait_for_selector(selector, timeout=15000, state="attached")
                print("Selector found!")
                count = await page.locator(selector).count()
                print(f"Count: {count}")
            except Exception as e:
                print(f"Selector wait failed: {e}")
                
            content = await page.content()
            with open("shay_jordan_debug.html", "w") as f:
                f.write(content)
            print("Saved debug HTML.")

if __name__ == "__main__":
    asyncio.run(test())
