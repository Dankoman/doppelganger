import argparse
import asyncio
import sqlite3
import os
import aiohttp
import re
import csv
import subprocess
import random
from pathlib import Path
from urllib.parse import urljoin
from camoufox.async_api import AsyncCamoufox
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.text import Text
from rich.align import Align

MAX_IMAGES_PER_MODEL = 50
API_ENDPOINT = "http://127.0.0.1:5000/recognize"
OUTPUT_DIR = Path("/home/marqs/Bilder/Nya")
FACE_EXTRACTOR_DIR = Path(__file__).parent.parent.parent / "face_extractor"
UNCERTAINTY_SCRIPT = FACE_EXTRACTOR_DIR / "model_uncertainty.py"
DB_PATH = FACE_EXTRACTOR_DIR / "arcface_work-ppic" / "processed.db"
EMB_PATH = FACE_EXTRACTOR_DIR / "arcface_work-ppic" / "embeddings_ppic.pkl"

class ScraperUI:
    def __init__(self, concurrency, total_models):
        self.console = Console()
        self.layout = Layout()
        self.total_models = total_models
        self.completed_models = 0
        self.total_images = 0
        self.logs = []
        self.worker_status = ["Väntar..."] * concurrency
        self.worker_models = ["-"] * concurrency
        
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=22)
        )
        self.layout["body"].split_row(
            Layout(name="workers", ratio=1),
            Layout(name="stats", size=30)
        )

    def log(self, message):
        self.logs.append(message)
        if len(self.logs) > 20:
            self.logs.pop(0)

    def update_worker(self, idx, model_name, status):
        self.worker_models[idx] = model_name
        self.worker_status[idx] = status

    def render(self):
        # Header
        header_text = Text(f"🚀 PornPics Scraper Dashboard | Modeller: {self.completed_models}/{self.total_models} | Bilder: {self.total_images}", 
                          style="bold white on blue", justify="center")
        self.layout["header"].update(Panel(Align.center(header_text)))

        # Workers Table
        table = Table(title="Aktiva Arbetare", expand=True)
        table.add_column("ID", width=4)
        table.add_column("Modell", style="magenta", width=25)
        table.add_column("Status", style="cyan")
        
        for i, (m, s) in enumerate(zip(self.worker_models, self.worker_status)):
            table.add_row(str(i+1), m, s)
        self.layout["workers"].update(Panel(table))

        # Stats Panel
        stats_text = Text(f"Klara: {self.completed_models}\nTotalt: {self.total_models}\nBilder: {self.total_images}\n\nQ: Ctrl+C för att avbryta", style="dim")
        self.layout["stats"].update(Panel(stats_text, title="Statistik"))

        # Logs Panel
        log_content = "\n".join(self.logs)
        self.layout["footer"].update(Panel(log_content, title="Senaste Händelser", border_style="white"))

        return self.layout

UI = None


def init_db(db_path=None):
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "ppic_scraper_state.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS models (
            name TEXT PRIMARY KEY,
            url TEXT,
            started INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            failed_attempts INTEGER DEFAULT 0
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
    try:
        cur.execute("ALTER TABLE models ADD COLUMN failed_attempts INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    return conn


async def safe_goto(page, url, wait_for_selector=None, timeout=60000, retries=2, label=""):
    global UI
    for attempt in range(retries + 1):
        try:
            goto_success = False
            try:
                # Använd 'commit' (när servern skickat headers) för att undvika att hänga på sega externa skript.
                response = await page.goto(url, wait_until="commit", timeout=timeout)
                if response and response.status == 404:
                    raise Exception("404 Not Found")
                goto_success = True
            except Exception as goto_err:
                if "Timeout" in str(goto_err) and wait_for_selector:
                    if UI: UI.log(f"  [{label}] Sidladdning (commit) timeade ut, men vi kollar om galleriet laddat ändå...")
                    # Försök stoppa laddningen så vi kan fortsätta med det som hunnit laddas
                    try:
                        await page.evaluate("window.stop()")
                    except:
                        pass
                else:
                    raise goto_err
            
            if wait_for_selector:
                # Vi väntar på elementet. Nu med lite mer generös timeout (30s) då vi vet att sidan kan vara seg.
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=30000, state="attached")
                except Exception as e:
                    # Om vi misslyckas efter commit-timeout, prova window.stop() en gång till och kolla igen
                    try:
                        await page.evaluate("window.stop()")
                    except:
                        pass
                    # En sista chans att hitta den ifall den precis dök upp
                    await page.wait_for_selector(wait_for_selector, timeout=5000, state="attached")
            elif not goto_success:
                raise Exception(f"Timeout vid laddning av {url}")
                
            return True
        except Exception as e:
            err_str = str(e)
            if "404 Not Found" in err_str:
                raise e
            if "Timeout" in err_str:
                phase = "väntan på selector" if "wait_for_selector" in err_str else "navigering"
                msg = f"Timeout under {phase}"
            else:
                msg = err_str

            if attempt < retries:
                if UI: UI.log(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")
                else: print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")
                try:
                    await page.evaluate("window.stop()")
                except:
                    pass
                await asyncio.sleep(random.uniform(3, 7))
            else:
                raise e
    return False


async def setup_resource_blocking(context):
    async def handle_route(route):
        req = route.request
        # Blockera kända annonsdomäner, trackers och tunga resurser som segar ner laddningen
        if any(x in req.url for x in [
            "google-analytics", "doubleclick", "googletagmanager", "yandex.ru", 
            "adnxs", "popads", "onclickads", "tsyndicate.com", "realsrv.com",
            "trafficstars.com", "exoclick.com", "juicyads.com", "m32.media",
            "hpacdn.pornpics.com/renderer", "rtmark.net", "vlyby.com"
        ]) or req.resource_type in ["image", "font", "media"]:
            return await route.abort()
        await route.continue_()
    
    await context.route("**/*", handle_route)


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
    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
                
                async with session.post(API_ENDPOINT + "?raw_faces=1&all_angles=1", data=data, timeout=30) as resp:
                    if resp.status != 200:
                        if resp.status == 503: # Tjänsten laddar om
                            raise aiohttp.ClientConnectorError(None, None)
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
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
            if attempt < max_retries - 1:
                print(f"  [API VÄNTAR] Servertjänsten är inte tillgänglig (omladdning pågår?). Försök {attempt+1}/{max_retries}...")
                await asyncio.sleep(5)
            else:
                print(f"  [API FEL] Kunde inte nå servertjänsten efter {max_retries} försök.")
                return "reject"
        except Exception as e:
            if UI: UI.log(f"  [API FEL] Oväntat fel vid validering: {e}")
            return "reject"
    return "reject"


async def download_image(page, url, model_name, gallery_url, worker_idx=0):
    db_conn = init_db()
    cur = db_conn.cursor()
    cur.execute("SELECT local_path, valid FROM images WHERE url = ?", (url,))
    row = cur.fetchone()
    if row is not None:
        db_conn.close()
        return "save" if row[1] == 1 else "reject"
        
    if UI: UI.update_worker(worker_idx, model_name, f"Laddar ner: {url[:40]}...")
    try:
        response = await page.request.get(url, headers={"Referer": page.url}, timeout=30000)
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
        if UI: 
            UI.total_images += 1
            UI.log(f"  [{model_name}] [SPARAD] {local_path.name}")
        return "save"
        
    except Exception as e:
        if UI: UI.log(f"  [{model_name}] [ERROR] {url}: {e}")
        db_conn.close()
        return "reject"


async def scrape_model_galleries(page, model_name, model_url, worker_idx=0):
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
    
    if UI: 
        UI.log(f"[{model_name}] -> Startar skrapning")
        UI.update_worker(worker_idx, model_name, "Laddar modellsida...")
    try:
        await safe_goto(page, model_url, wait_for_selector=GALLERY_SELECTOR, timeout=30000, label=model_name)
        
        # Kontrollera kön (Gender)
        try:
            if UI: UI.update_worker(worker_idx, model_name, "Kontrollerar kön...")
            gender_item = page.locator(".card-additional-info .item", has_text="Gender:").first
            
            # Ge den upp till 5 sekunder att dyka upp om den inte finns direkt
            try:
                await gender_item.wait_for(state="attached", timeout=5000)
            except:
                pass

            if await gender_item.count() > 0:
                gender_val = await gender_item.locator(".value").first.inner_text()
                gender_val = gender_val.strip()
                if "female" not in gender_val.lower():
                    if UI: UI.log(f"  [{model_name}] [SKIP] Kön verifierat som '{gender_val}', inte 'Female'.")
                    cur.execute("UPDATE models SET completed = 1 WHERE name = ?", (model_name,))
                    db_conn.commit()
                    db_conn.close()
                    if UI:
                        UI.completed_models += 1
                        UI.update_worker(worker_idx, "-", "Klar (Skippad)!")
                    return
            else:
                if UI: UI.log(f"  [{model_name}] [VARNING] Hittade inget fält för kön. Fortsätter.")
        except Exception as ge:
            if UI: UI.log(f"  [{model_name}] [VARNING] Kunde inte kontrollera kön: {ge}")

        if UI: UI.update_worker(worker_idx, model_name, "Söker efter fler gallerier...")
        await scroll_to_load_more(page, GALLERY_SELECTOR, 15, label=model_name)
    except Exception as e:
        if UI: UI.log(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")
        if "404 Not Found" in str(e):
            cur.execute("UPDATE models SET failed_attempts = failed_attempts + 10 WHERE name = ?", (model_name,))
        else:
            cur.execute("UPDATE models SET failed_attempts = failed_attempts + 1 WHERE name = ?", (model_name,))
        db_conn.commit()
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
            
        if UI: UI.update_worker(worker_idx, model_name, f"Öppnar galleri: {g_url[:40]}...")
        gallery_page = await page.context.new_page()
        try:
            await safe_goto(gallery_page, g_url, wait_for_selector="img", timeout=25000, label=model_name)
            await asyncio.sleep(1)
        except Exception as e:
            if UI: UI.log(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")
            await gallery_page.close()
            continue
            
        img_els = await gallery_page.locator("a, img").element_handles()
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
            
            status = await download_image(gallery_page, target_url, model_name, g_url, worker_idx=worker_idx)
            
            if status == "abort":
                if UI: UI.log(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")
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
            
        await gallery_page.close()

    cur.execute("UPDATE models SET completed = 1 WHERE name = ?", (model_name,))
    db_conn.commit()
    db_conn.close()
    if UI: 
        UI.completed_models += 1
        UI.update_worker(worker_idx, "-", "Klar!")
        UI.log(f"[{model_name}] Färdig med modell!")


async def main():
    import os
    try:
        total_cores = os.cpu_count()
        if total_cores and total_cores > 2:
            allowed_cores = set(range(total_cores - 2))
            os.sched_setaffinity(0, allowed_cores)
            print(f"⚙️ CPU-Affinity satt till {len(allowed_cores)}/{total_cores} kärnor (sparar 2 till OS).")
    except Exception:
        pass

    global MAX_IMAGES_PER_MODEL
    parser = argparse.ArgumentParser(description="Scrape poorly trained models from PornPics")
    parser.add_argument("--persons-per-run", type=int, default=20, help="Number of models to scrape")
    parser.add_argument("--images-per-person", type=int, default=50, help="Images per person max")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent models to scrape")
    parser.add_argument("--min-samples", type=int, default=5, help="Hoppa över personer som redan har minst detta antal lyckade bilder (om ej 'blandade')")
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
    report_file = Path(__file__).parent.parent / "data" / "temp_uncertainty_report.csv"
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

    flagged_critical = []
    flagged_normal = []
    skipped_count = 0
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rec = row.get("Recommendation", "")
                if "Namnen är nästan identiska" in rec or "MERGE: Slå ihop" in rec:
                    continue
                
                # Kontrollera om mappen är flaggad för "blandade identiteter" (varians)
                issue_a = row.get("Issue A", "")
                issue_b = row.get("Issue B", "")
                is_mixed_a = "varians" in issue_a.lower() or "blandade" in issue_a.lower() or "varians" in rec.lower() or "blandade" in rec.lower()
                is_mixed_b = "varians" in issue_b.lower() or "blandade" in issue_b.lower() or "varians" in rec.lower() or "blandade" in rec.lower()
                
                # Är det ett förväxlingspar? (Person B finns)
                name_b = row.get("Person B", "")
                is_confusion = bool(name_b)

                # Filtrera Person A
                name_a = row.get("Person A")
                if name_a:
                    samples_a = int(row.get("Samples A", "0") or "0")
                    if samples_a >= args.min_samples and not is_mixed_a and not is_confusion:
                        skipped_count += 1
                    else:
                        if is_mixed_a or is_confusion:
                            flagged_critical.append(name_a)
                        else:
                            flagged_normal.append(name_a)

                # Filtrera Person B (om den finns och inte redan är hanterad som A)
                if name_b:
                    samples_b = int(row.get("Samples B", "0") or "0")
                    if samples_b >= args.min_samples and not is_mixed_b and not is_confusion:
                        # Hoppa över om den har nog med samples och inte är i behov av kritisk fix
                        pass
                    else:
                        if is_mixed_b or is_confusion:
                            flagged_critical.append(name_b)
                        else:
                            flagged_normal.append(name_b)
    
    # Ta bort dubbletter men behåll ordning (critical först)
    seen = set()
    flagged_names = []
    for n in flagged_critical + flagged_normal:
        if n not in seen:
            flagged_names.append(n)
            seen.add(n)

    if skipped_count > 0:
        print(f"ℹ️  Hoppade över {skipped_count} personer som redan har >= {args.min_samples} bilder (och inte är flaggade som 'blandade' eller 'förväxling').")
    
    print(f"✅ Hittade {len(flagged_names)} potentiellt osäkra modeller ({len(flagged_critical)} kritiska). Letar vidare på PornPics...")

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

        models_to_queue = []
        for name in flagged_names:
            if not name:
                continue
            cur.execute("SELECT completed, failed_attempts FROM models WHERE name = ?", (name,))
            row = cur.fetchone()
            if row and row[0] == 1:
                continue # Redan behandlad

            failed_attempts = row[1] if row else 0

            if failed_attempts >= 3:
                print(f"  [SKIP] Hoppar över {name} då den misslyckats {failed_attempts} gånger tidigare.")
                continue

            lower_name = name.lower()
            m_url = list_links.get(lower_name)
            if not m_url:
                slug = lower_name.replace(" ", "-")
                m_url = f"https://www.pornpics.com/pornstars/{slug}/"

            models_to_queue.append((failed_attempts, name, m_url))
        
        models_to_queue.sort(key=lambda x: x[0])
        models_queue = asyncio.Queue()
        for fa, name, m_url in models_to_queue:
            models_queue.put_nowait((name, m_url))
        
        db_conn.close()

        if models_queue.empty():
            print("🚀 Inga nya modeller hittades att processa eller alla är markerade klara i databasen.")
            return

        target_count = min(args.persons_per_run, models_queue.qsize())
        print(f"🔄 Bearbetar upp till {target_count} modeller (från {models_queue.qsize()} i kö) med concurrency = {args.concurrency}")

        global UI
        UI = ScraperUI(args.concurrency, target_count)

        async def worker(idx):
            while True:
                if UI and UI.completed_models >= target_count:
                    UI.update_worker(idx, "-", "Uppnått mål!")
                    break
                
                try:
                    n, u = models_queue.get_nowait()
                except asyncio.QueueEmpty:
                    UI.update_worker(idx, "-", "Inga fler modeller!")
                    break

                delay = random.uniform(2, 6)
                if UI: UI.update_worker(idx, n, f"Väntar {delay:.1f}s...")
                await asyncio.sleep(delay)
                
                cur_task = None
                try:
                    cur_task = init_db()
                    c = cur_task.cursor()
                    c.execute("INSERT OR IGNORE INTO models (name, url) VALUES (?, ?)", (n, u))
                    cur_task.commit()
                    
                    async with await browser.new_context() as context:
                        await setup_resource_blocking(context)
                        w_page = await context.new_page()
                        try:
                            await scrape_model_galleries(w_page, n, u, worker_idx=idx)
                        finally:
                            await w_page.close()
                except Exception as e:
                    if UI: UI.log(f"🔴 [{n}] Kritiskt fel i worker: {e}")
                finally:
                    if cur_task:
                        cur_task.close()
                    models_queue.task_done()
        
        tasks = [worker(i) for i in range(args.concurrency)]
        
        with Live(UI.render(), refresh_per_second=4, screen=False) as live:
            # Uppdatera Live-objektet periodiskt
            async def ui_updater():
                while True:
                    live.update(UI.render())
                    await asyncio.sleep(0.25)
            
            updater_task = asyncio.create_task(ui_updater())
            try:
                if tasks:
                    await asyncio.gather(*tasks)
            finally:
                updater_task.cancel()

    print("✅ Skrapning avslutades framgångsrikt.")

if __name__ == "__main__":
    asyncio.run(main())
