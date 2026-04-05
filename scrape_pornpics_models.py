import argparse
import asyncio
import sqlite3
import os
import aiohttp
import re
from pathlib import Path
from urllib.parse import urljoin
from camoufox.async_api import AsyncCamoufox

MAX_IMAGES_PER_MODEL = 50
API_ENDPOINT = "http://127.0.0.1:5000/recognize"
START_URL = "https://www.pornpics.com/tags/innie-pussy/"
OUTPUT_DIR = Path("/home/marqs/Bilder/Innie")


def init_db(db_path="scraper_state.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")  # Förbättrad prestanda vid parallell körning
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
    # Säkerställ att gamla databaser får gallery_url-kolumnen
    try:
        cur.execute("ALTER TABLE images ADD COLUMN gallery_url TEXT;")
    except sqlite3.OperationalError:
        pass # Kolumnen finns redan
        
    conn.commit()
    return conn


async def safe_goto(page, url, wait_for_selector=None, timeout=60000, retries=2, label=""):
    """
    Säkrare navigering med retry och alternativ väntestrategi.
    Använder 'commit' för initial navigering och väntar sedan på en selector ifall domcontentloaded hänger.
    """
    for attempt in range(retries + 1):
        try:
            # Vi väntar på 'commit' (när servern skickat headern) och sen manuellt på innehåll
            await page.goto(url, wait_until="commit", timeout=timeout)
            
            # Ge sidan en liten stund att faktiskt börja rendera om det behövs
            await asyncio.sleep(1)
            
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=20000, state="attached")
            else:
                # Fallback: vänta på något generellt som indikerar att sidan är laddad
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                except:
                    pass # Vi fortsätter ändå om vi har innehåll
            
            return True
        except Exception as e:
            if attempt < retries:
                print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {e}")
                await asyncio.sleep(2)
            else:
                raise e
    return False


async def scroll_to_load_more(page, selector, target_count, max_scrolls=40, label=""):
    """Scrollar ner tills target_count element som matchar selector hittas, eller till stagnation."""
    last_height = await page.evaluate("document.body.scrollHeight")
    last_count = 0
    stagnation_count = 0
    
    for i in range(max_scrolls):
        count = await page.locator(selector).count()
        if count >= target_count:
            break
            
        # Om vi inte hittade fler element efter en scroll, räkna stagnation
        if count == last_count and count > 0:
            stagnation_count += 1
            if stagnation_count >= 3: # Prova 3 gånger ifall det är segt
                if label: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")
                break
        else:
            stagnation_count = 0
            
        last_count = count
            
        if label and i % 5 == 0:
            print(f"  [{label}] Scrollar för mer innehåll... ({count}/{target_count})")
            
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2.5) # PornPics behöver lite tid att ladda
        
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            # Prova en extra gång ifall det var segt
            await asyncio.sleep(2)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break 
        last_height = new_height


async def validate_image(image_bytes: bytes) -> str:
    """
    Validerar bilden och returnerar status:
    'save'  -> 0-1 kvinna, 0 män.
    'abort' -> >1 kvinna (Nuka hela galleriet).
    'reject'-> Innehåller män eller andra fel.
    """
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
                    return "save"  # 0 ansikten är OK enligt användaren
                
                female_count = 0
                male_count = 0
                for f in faces:
                    prob = f.get("female_probability")
                    if prob is not None and prob >= 0.60:
                        female_count += 1
                    else:
                        male_count += 1
                
                # 1. Kritiskt: Fler än en kvinna? Nuka galleriet!
                if female_count > 1:
                    return "abort"
                
                # 2. Innehåller män? Avvisa bilden men tillåt galleriet fortsätta
                if male_count > 0:
                    return "reject"
                
                # 3. Solobild (0-1 kvinna, 0 män) - Spara!
                return "save"
                
    except Exception as e:
        print(f"  [API FEL] {e}")
        return "reject"


async def download_image(page, url, model_name, gallery_url):
    """
    Laddar ner en bild och validerar den.
    Returnerar validerings-status ('save', 'abort', 'reject').
    """
    db_conn = init_db()  # Varje worker/task har egen anslutning
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
            
        # Sparar filen om godkänd
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
    """Hittar gallerier för en specifik modell, och laddar ner bilder till MAX."""
    db_conn = init_db()
    cur = db_conn.cursor()
    cur.execute('UPDATE models SET started = 1 WHERE name = ?', (model_name,))
    db_conn.commit()
    
    # Selektor för gallerier som tillhör den aktuella listan (undvik sökförslag)
    GALLERY_SELECTOR = "li.thumbwook a[href*='/galleries/']"
    
    def get_local_image_count():
        model_dir = OUTPUT_DIR / model_name
        if not model_dir.exists():
            return 0
        return len(list(model_dir.glob("*.jpg")))
    
    current_page_idx = 1
    
    # Hitta gallerier via oändlig scroll
    print(f"[{model_name}] -> Letar gallerier via scroll på {model_url}")
    try:
        # På modellsidor väntar vi på galleri-länkar
        await safe_goto(page, model_url, wait_for_selector=GALLERY_SELECTOR, timeout=60000, label=model_name)
        # Vi scrollar tills vi har tillräckligt med gallerier för att nå 50 bilder (ca 5 gallerier räcker oftast, men vi tar 15 för säkerhets skull)
        await scroll_to_load_more(page, GALLERY_SELECTOR, 15, label=model_name)
    except Exception as e:
        print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")
        db_conn.close()
        return

    # Hitta alla galleriboxar
    links = await page.locator(GALLERY_SELECTOR).element_handles()
    
    for link in links:
        if get_local_image_count() >= MAX_IMAGES_PER_MODEL:
            break

        img_el = await link.query_selector("img")
        if not img_el: continue
            
        alt_text = await img_el.get_attribute("alt")
        if not alt_text: continue
        
        # Filter
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

    # Processa gallerierna vi hittat
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
                # ... radera logik ...
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

    # Kontrollera slutförd
    cur.execute("UPDATE models SET completed = 1 WHERE name = ?", (model_name,))
    db_conn.commit()
    db_conn.close()
    print(f"[{model_name}] Färdig med modell!")
        

async def main():
    global MAX_IMAGES_PER_MODEL
    parser = argparse.ArgumentParser(description="PornPics Model Image Scraper")
    parser.add_argument("--persons-per-run", type=int, default=10, help="Number of limits for downloaded models per run")
    parser.add_argument("--images-per-person", type=int, default=50, help="Number of images to download per person")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent models to scrape")
    parser.add_argument("--wipe-db", action="store_true", help="Clear the database progress before starting")
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

    async with AsyncCamoufox(headless=True) as browser:
        semaphore = asyncio.Semaphore(args.concurrency)
        processed_models = set()
        models_to_process = []
        
        page = await browser.new_page()
        print(f"🔍 Letar efter modeller på tag-sidan via scroll: {START_URL}")
        visited_galleries = set()
        try:
            await safe_goto(page, START_URL, wait_for_selector="a[href*='/galleries/']", label="Discovery")
            
            while len(models_to_process) < args.persons_per_run:
                gallery_links = await page.locator("a[href*='/galleries/']").element_handles()
                new_found_in_batch = 0
                
                for g_link in gallery_links:
                    if len(models_to_process) >= args.persons_per_run:
                        break
                    
                    g_href = await g_link.get_attribute("href")
                    if not g_href: continue
                    g_url = urljoin(START_URL, g_href)
                    
                    if g_url in visited_galleries:
                        continue
                    
                    visited_galleries.add(g_url)
                    new_found_in_batch += 1
                    
                    # Öppna galleri för att hitta modeller
                    g_page = await browser.new_page()
                    try:
                        # Ökad timeout till 60s för att vara mer tålig mot sega anslutningar
                        await safe_goto(g_page, g_url, wait_for_selector=".gallery-info__content", timeout=60000, label="Extraction")
                        model_links = await g_page.locator(".gallery-info__content a[href*='/pornstars/']").element_handles()
                        
                        for m_link in model_links:
                            name = (await m_link.inner_text()).strip()
                            href = await m_link.get_attribute("href")
                            if name and href and name not in processed_models:
                                m_url = urljoin(START_URL, href)
                                cur.execute("SELECT completed FROM models WHERE name = ?", (name,))
                                row = cur.fetchone()
                                if not row or row[0] == 0:
                                    # Spara till DB omedelbart så vi inte tappar framsteg om vi avbryter
                                    cur.execute("INSERT OR IGNORE INTO models (name, url) VALUES (?, ?)", (name, m_url))
                                    db_conn.commit()
                                    
                                    models_to_process.append((name, m_url))
                                    processed_models.add(name)
                                    print(f"    [FUNNEN] {name} ({len(models_to_process)}/{args.persons_per_run})")
                            
                            if len(models_to_process) >= args.persons_per_run:
                                break
                    except Exception as e:
                        print(f"    [Extraction] Misslyckades med galleri: {e}")
                    finally:
                        await g_page.close()
                        await asyncio.sleep(1.0) # Stealth-delay för att inte hamra servern oavbrutet

                if len(models_to_process) < args.persons_per_run:
                    current_count = len(gallery_links)
                    print(f"  [Discovery] Hittat {len(models_to_process)}/{args.persons_per_run} modeller. Scrollar för fler gallerier...")
                    await scroll_to_load_more(page, "a[href*='/galleries/']", current_count + 12, label="Discovery")
                    
                    # Kolla om vi faktiskt hittade fler
                    new_count = await page.locator("a[href*='/galleries/']").count()
                    if new_count <= current_count:
                        print(f"  [Discovery] Inga fler gallerier hittades. Avbryter sökning.")
                        break
        except Exception as e:
            print(f"    [VARNING] Fel vid sökning: {e}")
        
        await page.close()
        db_conn.close() 
        
        async def worker(name, url):
            async with semaphore:
                # Slumpmässig fördröjning för att undvika samtidig start-detektering
                import random
                delay = random.uniform(2, 8)
                print(f"  [{name}] Väntar {delay:.1f}s innan start...")
                await asyncio.sleep(delay)
                
                cur_task = None
                try:
                    cur_task = init_db()
                    c = cur_task.cursor()
                    c.execute("INSERT OR IGNORE INTO models (name, url) VALUES (?, ?)", (name, url))
                    cur_task.commit()
                    
                    # Använd ny browser context för total isolering (cookies, fingerprint etc)
                    async with await browser.new_context() as context:
                        w_page = await context.new_page()
                        try:
                            await scrape_model_galleries(w_page, name, url)
                        finally:
                            await w_page.close()
                except Exception as e:
                    print(f"🔴 [{name}] Kritiskt fel i worker: {e}")
                finally:
                    if cur_task:
                        cur_task.close()

        tasks = [worker(n, u) for n, u in models_to_process]
        if tasks:
            await asyncio.gather(*tasks)
            
    print("Skrapning avslutades framgångsrikt.")

if __name__ == "__main__":
    asyncio.run(main())
