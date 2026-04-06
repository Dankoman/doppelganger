import argparse
import asyncio
import sqlite3
import os
import aiohttp
import re
import csv
import subprocess
from pathlib import Path
from urllib.parse import urljoin
from camoufox.async_api import AsyncCamoufox

MAX_IMAGES_PER_MODEL = 50
API_ENDPOINT = "http://127.0.0.1:5000/recognize"
OUTPUT_DIR = Path("/home/marqs/Bilder/Nya")
UNCERTAINTY_SCRIPT = Path("/home/marqs/Programmering/Python/3.11/face_extractor/model_uncertainty.py")
DB_PATH = Path("/home/marqs/Programmering/Python/3.11/face_extractor/arcface_work-ppic/processed.db")
EMB_PATH = Path("/home/marqs/Programmering/Python/3.11/face_extractor/arcface_work-ppic/embeddings_ppic.pkl")


def init_db(db_path="uncertain_scraper_state.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS models (
            name TEXT PRIMARY KEY,
            url TEXT,
            started INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS galleries (
            url TEXT PRIMARY KEY,
            model_name TEXT,
            processed INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS images (
            url TEXT PRIMARY KEY,
            model_name TEXT,
            gallery_url TEXT,
            local_path TEXT,
            valid INTEGER DEFAULT 1
        )
    ''')
    try:
        cur.execute("ALTER TABLE images ADD COLUMN gallery_url TEXT;")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    return conn


async def safe_goto(page, url, wait_for_selector=None, timeout=60000, retries=2, label=""):
    for attempt in range(retries + 1):
        try:
            await page.goto(url, wait_until="commit", timeout=timeout)
            await asyncio.sleep(1)
            
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=20000, state="attached")
            else:
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass
            return True
        except Exception as e:
            if attempt < retries:
                print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {e}")
                await asyncio.sleep(2)
            else:
                raise e
    return False


async def scroll_to_load_more(page, selector, target_count, max_scrolls=40, label=""):
    last_height = await page.evaluate("document.body.scrollHeight")
    last_count = 0
    stagnation_count = 0
    
    for i in range(max_scrolls):
        count = await page.locator(selector).count()
        if count >= target_count:
            break
            
        if count == last_count and count > 0:
            stagnation_count += 1
            if stagnation_count >= 3:
                if label: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")
                break
        else:
            stagnation_count = 0
            
        last_count = count
            
        if label and i % 5 == 0:
            print(f"  [{label}] Scrollar för mer innehåll... ({count}/{target_count})")
            
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2.5)
        
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            await asyncio.sleep(2)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break 
        last_height = new_height


async def validate_image(image_bytes: bytes) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
            
            async with session.post(API_ENDPOINT + "?raw_faces=1&all_angles=1", data=data, timeout=25) as resp:
                if resp.status != 200:
                    return "reject"
                
                faces = await resp.json()
                if not isinstance(faces, list):
                    return "reject"
                
                if len(faces) == 0:
                    return "save"
                
                female_count = 0
                male_count = 0
                for f in faces:
                    prob = f.get("female_probability")
                    if prob is not None and prob >= 0.60:
                        female_count += 1
                    else:
                        male_count += 1
                
                if female_count > 1:
                    return "abort"
                if male_count > 0:
                    return "reject"
                
                return "save"
    except Exception as e:
        print(f"  [API FEL] {e}")
        return "reject"


async def download_image(page, url, model_name, gallery_url):
    db_conn = init_db()
    cur = db_conn.cursor()
    cur.execute("SELECT local_path, valid FROM images WHERE url = ?", (url,))
    row = cur.fetchone()
    if row is not None:
        db_conn.close()
        return "save" if row[1] == 1 else "reject"
        
    print(f"  [{model_name}] Laddar ner: {url}")
    try:
        response = await page.request.get(url, headers={"Referer": page.url}, timeout=60000)
        if response.status != 200:
            db_conn.close()
            return "reject"
            
        img_bytes = await response.body()
        status = await validate_image(img_bytes)
        
        if status != "save":
            cur.execute("INSERT OR REPLACE INTO images (url, model_name, gallery_url, local_path, valid) VALUES (?, ?, ?, ?, ?)",
                        (url, model_name, gallery_url, "", 0))
            db_conn.commit()
            db_conn.close()
            return status
            
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        model_dir = OUTPUT_DIR / model_name
        model_dir.mkdir(exist_ok=True)
        
        file_name = url.split('/')[-1]
        local_path = model_dir / file_name
        
        with open(local_path, "wb") as f:
            f.write(img_bytes)
            
        cur.execute("INSERT OR REPLACE INTO images (url, model_name, gallery_url, local_path, valid) VALUES (?, ?, ?, ? , ?)",
                    (url, model_name, gallery_url, str(local_path), 1))
        db_conn.commit()
        db_conn.close()
        print(f"  [{model_name}] [SPARAD] {local_path}")
        return "save"
        
    except Exception as e:
        print(f"  [{model_name}] [ERROR] {url}: {e}")
        db_conn.close()
        return "reject"


async def scrape_model_galleries(page, model_name, model_url):
    db_conn = init_db()
    cur = db_conn.cursor()
    cur.execute('UPDATE models SET started = 1 WHERE name = ?', (model_name,))
    db_conn.commit()
    
    GALLERY_SELECTOR = "li.thumbwook a[href*='/galleries/']"
    
    def get_local_image_count():
        model_dir = OUTPUT_DIR / model_name
        if not model_dir.exists():
            return 0
        return len(list(model_dir.glob("*.jpg")))
    
    print(f"[{model_name}] -> Letar gallerier på {model_url}")
    try:
        await safe_goto(page, model_url, wait_for_selector=GALLERY_SELECTOR, timeout=60000, label=model_name)
        await scroll_to_load_more(page, GALLERY_SELECTOR, 15, label=model_name)
    except Exception as e:
        print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")
        db_conn.close()
        return

    links = await page.locator(GALLERY_SELECTOR).element_handles()
    
    for link in links:
        if get_local_image_count() >= MAX_IMAGES_PER_MODEL:
            break

        img_el = await link.query_selector("img")
        if not img_el: continue
            
        alt_text = await img_el.get_attribute("alt")
        if not alt_text: continue
        
        title_lower = alt_text.lower()
        forbidden = ["lesbian", "les", "ffm", "fffm", "ffmm", "orgy", "gangbang", "gb"]
        if any(re.search(fr'\b{word}\b', title_lower) for word in forbidden):
            continue
            
        if model_name.lower() in title_lower:
            gallery_href = await link.get_attribute("href")
            if not gallery_href: continue
            gallery_url = urljoin(model_url, gallery_href)
            
            cur.execute("SELECT processed FROM galleries WHERE url = ?", (gallery_url,))
            g_row = cur.fetchone()
            if g_row and (g_row[0] == 1 or g_row[0] == -1): continue
                
            cur.execute("INSERT OR IGNORE INTO galleries (url, model_name) VALUES (?, ?)", (gallery_url, model_name))
            db_conn.commit()

    cur.execute("SELECT url FROM galleries WHERE model_name = ? AND processed = 0", (model_name,))
    galleries = cur.fetchall()
    
    for (g_url,) in galleries:
        if get_local_image_count() >= MAX_IMAGES_PER_MODEL:
            break
            
        print(f" [{model_name}] -> Öppnar galleri: {g_url}")
        try:
            await safe_goto(page, g_url, wait_for_selector="img", timeout=45000, label=model_name)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")
            continue
            
        img_els = await page.locator("a, img").element_handles()
        image_urls = []
        for el in img_els:
            href = await el.get_attribute("href")
            if href and "cdni.pornpics.com" in href and href.endswith(".jpg"):
                image_urls.append(href)
                continue
            src = await el.get_attribute("data-src") or await el.get_attribute("src")
            if src and "cdni.pornpics.com" in src and src.endswith(".jpg"):
                image_urls.append(src)

        best_images = {}
        for u in set(image_urls):
            filename = u.split('/')[-1]
            if not filename or not filename.endswith(".jpg"):
                continue
            is_highres = "/460/" not in u
            if filename not in best_images or (is_highres and "/460/" in best_images[filename]):
                best_images[filename] = u

        for i_url in best_images.values():
            if get_local_image_count() >= MAX_IMAGES_PER_MODEL:
                break
            
            target_url = i_url
            if "/460/" in target_url:
                target_url = target_url.replace("/460/", "/1280/")
            
            status = await download_image(page, target_url, model_name, g_url)
            
            if status == "abort":
                print(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")
                cur.execute("SELECT local_path FROM images WHERE gallery_url = ? AND local_path != ''", (g_url,))
                for (p,) in cur.fetchall():
                    if os.path.exists(p): os.remove(p)
                cur.execute("DELETE FROM images WHERE gallery_url = ?", (g_url,))
                cur.execute("UPDATE galleries SET processed = -1 WHERE url = ?", (g_url,))
                db_conn.commit()
                break
                
            await asyncio.sleep(0.5)
        
        cur.execute("SELECT processed FROM galleries WHERE url = ?", (g_url,))
        if cur.fetchone()[0] == 0:
            cur.execute("UPDATE galleries SET processed = 1 WHERE url = ?", (g_url,))
            db_conn.commit()

    cur.execute("UPDATE models SET completed = 1 WHERE name = ?", (model_name,))
    db_conn.commit()
    db_conn.close()
    print(f"[{model_name}] Färdig med modell!")


async def main():
    global MAX_IMAGES_PER_MODEL
    parser = argparse.ArgumentParser(description="Scrape poorly trained models from PornPics")
    parser.add_argument("--persons-per-run", type=int, default=20, help="Number of models to scrape")
    parser.add_argument("--images-per-person", type=int, default=50, help="Images per person max")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent models to scrape")
    parser.add_argument("--wipe-db", action="store_true", help="Rensa databasen innan körning")
    args = parser.parse_args()

    MAX_IMAGES_PER_MODEL = args.images_per_person

    db_conn = init_db()
    cur = db_conn.cursor()
    if args.wipe_db:
        print("🧹 Rensar all framstegshistorik från databasen (--wipe-db)...")
        cur.execute("DELETE FROM models")
        cur.execute("DELETE FROM galleries")
        cur.execute("DELETE FROM images")
        db_conn.commit()

    # Steg 1: Kör analysen för att få osäkra modeller
    print("🔍 Skapar osäkerhets-rapport med face_extractor...")
    report_file = "temp_uncertainty_report.csv"
    cmd = [
        "python3", str(UNCERTAINTY_SCRIPT),
        "--db", str(DB_PATH),
        "--embeddings", str(EMB_PATH),
        "--output", report_file,
        "--top", "800",
        "--exclusions", str(UNCERTAINTY_SCRIPT.parent / "similar_exclusions.txt"),
        "--ignore", str(UNCERTAINTY_SCRIPT.parent / "uncertainty_exceptions.txt")
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Analysen misslyckades: {e}")
        return

    flagged_names = set()
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rec = row.get("Recommendation", "")
                if "Namnen är nästan identiska" in rec or "MERGE: Slå ihop" in rec:
                    continue
                
                if row.get("Person A"): flagged_names.add(row["Person A"])
                if row.get("Person B"): flagged_names.add(row["Person B"])
    
    print(f"✅ Hittade {len(flagged_names)} potentiellt osäkra modeller. Letar vidare på PornPics...")

    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        print("🌍 Laddar listan över Pornstjärnor för att matcha adresser...")
        await safe_goto(page, "https://www.pornpics.com/pornstars/list/", label="MapNames")
        
        list_links = await page.evaluate('''() => {
            const links = document.querySelectorAll("a[href*='/pornstars/']");
            const map = {};
            for (let a of links) {
                if(a.innerText) {
                    map[a.innerText.trim().toLowerCase()] = a.href;
                }
            }
            return map;
        }''')
        await page.close()

        models_to_process = []
        for name in flagged_names:
            if not name:
                continue
            cur.execute("SELECT completed FROM models WHERE name = ?", (name,))
            row = cur.fetchone()
            if row and row[0] == 1:
                continue # Redan behandlad

            lower_name = name.lower()
            m_url = list_links.get(lower_name)
            if not m_url:
                slug = lower_name.replace(" ", "-")
                m_url = f"https://www.pornpics.com/pornstars/{slug}/"

            models_to_process.append((name, m_url))
            if len(models_to_process) >= args.persons_per_run:
                break
        
        db_conn.close()

        if not models_to_process:
            print("🚀 Inga nya modeller hittades att processa eller alla är markerade klara i databasen.")
            return

        print(f"🔄 Bearbetar {len(models_to_process)} modeller med concurrency = {args.concurrency}")

        semaphore = asyncio.Semaphore(args.concurrency)

        async def worker(n, u):
            async with semaphore:
                import random
                delay = random.uniform(2, 6)
                print(f"  [{n}] Väntar {delay:.1f}s innan start...")
                await asyncio.sleep(delay)
                
                cur_task = None
                try:
                    cur_task = init_db()
                    c = cur_task.cursor()
                    c.execute("INSERT OR IGNORE INTO models (name, url) VALUES (?, ?)", (n, u))
                    cur_task.commit()
                    
                    async with await browser.new_context() as context:
                        w_page = await context.new_page()
                        try:
                            await scrape_model_galleries(w_page, n, u)
                        finally:
                            await w_page.close()
                except Exception as e:
                    print(f"🔴 [{n}] Kritiskt fel i worker: {e}")
                finally:
                    if cur_task:
                        cur_task.close()

        tasks = [worker(n, u) for n, u in models_to_process]
        if tasks:
            await asyncio.gather(*tasks)

    print("✅ Skrapning avslutades framgångsrikt.")

if __name__ == "__main__":
    asyncio.run(main())
