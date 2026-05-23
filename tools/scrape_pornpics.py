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
        header_text = Text(f"🚀 PornPics Scraper Dashboard | Modeller: {self.completed_models}/{self.total_models} | Bilder: {self.total_images}", 
                          style="bold white on blue", justify="center")
        self.layout["header"].update(Panel(Align.center(header_text)))

        table = Table(title="Aktiva Arbetare", expand=True)
        table.add_column("ID", width=4)
        table.add_column("Modell", style="magenta", width=25)
        table.add_column("Status", style="cyan")
        
        for i, (m, s) in enumerate(zip(self.worker_models, self.worker_status)):
            table.add_row(str(i+1), m, s)
        self.layout["workers"].update(Panel(table))

        stats_text = Text(f"Klara: {self.completed_models}\nTotalt: {self.total_models}\nBilder: {self.total_images}\n\nQ: Ctrl+C för att avbryta", style="dim")
        self.layout["stats"].update(Panel(stats_text, title="Statistik"))

        log_content = "\n".join(self.logs)
        self.layout["footer"].update(Panel(log_content, title="Senaste Händelser", border_style="white"))

        return self.layout

UI = None

# Lägg till face_extractor till sys.path så vi kan importera IdentityResolver
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "face_extractor"))
from identity_resolver import IdentityResolver
import builtins

def xprint(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    if UI is not None:
        if "Laddar ner" in msg or "Letar gallerier på" in msg or "Öppnar galleri" in msg or "[SPARAD]" in msg or "Färdig med modell" in msg or "[SKIP]" in msg:
            # We can't update individual worker here since we don't have worker_idx.
            # But we can at least log everything to the footer instead of messing up the UI.
            UI.log(msg)
            if "[SPARAD]" in msg:
                UI.total_images += 1
            if "Färdig med modell" in msg or "[SKIP] Kön verifierat" in msg:
                UI.completed_models += 1
        else:
            UI.log(msg)
    else:
        builtins.print(*args, **kwargs)

# --- Konfiguration ---
API_ENDPOINT = "http://127.0.0.1:5000/recognize"
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "ppic_scraper_state.db"
FACE_EXTRACTOR_DIR = Path(__file__).parent.parent.parent / "face_extractor"
UNCERTAINTY_SCRIPT = FACE_EXTRACTOR_DIR / "model_uncertainty.py"
PROCESSED_DB = FACE_EXTRACTOR_DIR / "arcface_work-ppic" / "processed.db"
EMBEDDINGS_PATH = FACE_EXTRACTOR_DIR / "arcface_work-ppic" / "embeddings_ppic.pkl"
DEFAULT_LIBRARY = Path("/home/marqs/Bilder/pBook")

TAG_ALIASES = {
    "innie": "https://www.pornpics.com/tags/innie-pussy/",
    "pussy": "https://www.pornpics.com/tags/pussy/",
    "closeup": "https://www.pornpics.com/tags/close-up/",
}

class PornPicsScraper:
    def __init__(self, output_dir, db_path, concurrency=3, images_per_person=50, library_dir=None, scorched_earth=False):
        self.output_dir = Path(output_dir)
        self.db_path = Path(db_path)
        self.library_dir = Path(library_dir) if library_dir else None
        self.concurrency = concurrency
        self.images_per_person = images_per_person
        self.scorched_earth = scorched_earth
        self.resolver = IdentityResolver(
            FACE_EXTRACTOR_DIR / "merge.txt",
            FACE_EXTRACTOR_DIR / "similar_exclusions.txt"
        )
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
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
        conn.close()

    def get_db(self):
        return sqlite3.connect(self.db_path)

    def is_model_done(self, name, canonical, force_rescrape=False):
        if force_rescrape:
            return False

        # 1. Kolla disk
        if (self.output_dir / canonical).exists():
            return True
        if self.library_dir and (self.library_dir / canonical).exists():
            return True
        
        # 2. Kolla databas
        db = self.get_db()
        cur = db.cursor()
        # Vi kollar både namnet från taggen och det kanoniska namnet
        cur.execute("SELECT completed FROM models WHERE name = ? OR name = ?", (name, canonical))
        row = cur.fetchone()
        db.close()
        
        if row and row[0] == 1:
            return True
        return False

    def get_failed_attempts(self, name, canonical):
        db = self.get_db()
        cur = db.cursor()
        cur.execute("SELECT failed_attempts FROM models WHERE name = ? OR name = ?", (name, canonical))
        rows = cur.fetchall()
        db.close()
        if not rows: return 0
        return max([r[0] for r in rows if r[0] is not None] + [0])

    async def safe_goto(self, page, url, wait_for_selector=None, timeout=60000, retries=2, label=""):
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
                        xprint(f"  [{label}] Sidladdning (commit) timeade ut, men vi kollar om galleriet laddat ändå...")
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
                # Snyggare felmeddelanden för timeouts
                if "Timeout" in err_str:
                    phase = "väntan på selector" if "wait_for_selector" in err_str else "navigering"
                    msg = f"Timeout under {phase}"
                else:
                    msg = err_str

                if attempt < retries:
                    xprint(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")
                    # Mer generös och slumpmässig väntan mellan retries
                    await asyncio.sleep(random.uniform(3, 7))
                else:
                    raise e
        return False

    async def scroll_to_load_more(self, page, selector, target_count, max_scrolls=40, label=""):
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
                    if label: xprint(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")
                    break
            else:
                stagnation_count = 0
            last_count = count
            if label and i % 5 == 0:
                xprint(f"  [{label}] Scrollar för mer innehåll... ({count}/{target_count})")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                await asyncio.sleep(2)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break 
            last_height = new_height

    async def setup_resource_blocking(self, context, allow_images=False):
        async def handle_route(route):
            req = route.request
            # Blockera kända annonsdomäner, trackers och tunga resurser som segar ner laddningen
            if any(x in req.url for x in [
                "google-analytics", "doubleclick", "googletagmanager", "yandex.ru", 
                "adnxs", "popads", "onclickads", "tsyndicate.com", "realsrv.com",
                "trafficstars.com", "exoclick.com", "juicyads.com", "m32.media",
                "hpacdn.pornpics.com/renderer", "rtmark.net", "vlyby.com"
            ]):
                return await route.abort()
            
            # Blockera tunga mediaresurser om de inte uttryckligen tillåtits
            if not allow_images and req.resource_type in ["image", "media", "font"]:
                return await route.abort()
            
            await route.continue_()
        
        await context.route("**/*", handle_route)

    async def validate_image(self, image_bytes: bytes) -> str:
        max_retries = 5
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Lägg till korta timeouts för att snabbt upptäcka om tjänsten är nere
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
                        
                        if male_count > 0:
                            return "reject"
                        if female_count > 1:
                            return "abort" if self.scorched_earth else "save"
                        
                        return "save"
            except (aiohttp.ClientConnectorError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError):
                if attempt < max_retries - 1:
                    xprint(f"  [API VÄNTAR] Servertjänsten är inte tillgänglig (omladdning pågår?). Försök {attempt+1}/{max_retries}...")
                    await asyncio.sleep(5)
                else:
                    xprint(f"  [API FEL] Kunde inte nå servertjänsten efter {max_retries} försök.")
                    return "reject"
            except Exception as e:
                xprint(f"  [API FEL] Oväntat fel vid validering: {e}")
                return "reject"
        return "reject"

    async def download_image(self, page, url, model_name, gallery_url):
        db_conn = self.get_db()
        cur = db_conn.cursor()
        cur.execute("SELECT local_path, valid FROM images WHERE url = ?", (url,))
        row = cur.fetchone()
        if row is not None:
            db_conn.close()
            return "save" if row[1] == 1 else "reject"
        xprint(f"  [{model_name}] Laddar ner: {url}")
        try:
            response = await page.request.get(url, headers={"Referer": page.url}, timeout=60000)
            if response.status != 200:
                db_conn.close()
                return "reject"
            img_bytes = await response.body()
            status = await self.validate_image(img_bytes)
            if status != "save":
                cur.execute("INSERT OR REPLACE INTO images (url, model_name, gallery_url, local_path, valid) VALUES (?, ?, ?, ?, ?)",
                            (url, model_name, gallery_url, "", 0))
                db_conn.commit()
                db_conn.close()
                return status
            self.output_dir.mkdir(parents=True, exist_ok=True)
            model_dir = self.output_dir / model_name
            model_dir.mkdir(exist_ok=True)
            file_name = url.split('/')[-1]
            local_path = model_dir / file_name
            with open(local_path, "wb") as f:
                f.write(img_bytes)
            cur.execute("INSERT OR REPLACE INTO images (url, model_name, gallery_url, local_path, valid) VALUES (?, ?, ?, ? , ?)",
                        (url, model_name, gallery_url, str(local_path), 1))
            db_conn.commit()
            db_conn.close()
            xprint(f"  [{model_name}] [SPARAD] {local_path}")
            return "save"
        except Exception as e:
            xprint(f"  [{model_name}] [ERROR] {url}: {e}")
            db_conn.close()
            return "reject"

    async def scrape_model_galleries(self, page, model_name, model_url):
        db_conn = self.get_db()
        cur = db_conn.cursor()
        # Säkerställ att modellen finns i DB innan vi uppdaterar status
        cur.execute('INSERT OR IGNORE INTO models (name, url) VALUES (?, ?)', (model_name, model_url))
        cur.execute('UPDATE models SET started = 1 WHERE name = ?', (model_name,))
        db_conn.commit()

        GALLERY_SELECTOR = "li.thumbwook a[href*='/galleries/']"
        def get_local_image_count():
            model_dir = self.output_dir / model_name
            if not model_dir.exists():
                return 0
            return len(list(model_dir.glob("*.jpg")))

        xprint(f"[{model_name}] -> Letar gallerier på {model_url}")
        try:
            await self.safe_goto(page, model_url, wait_for_selector=GALLERY_SELECTOR, timeout=60000, label=model_name)
            
            # Kontrollera kön (Gender)
            try:
                # Vänta en kort stund på att infokortet faktiskt dyker upp
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
                        xprint(f"  [{model_name}] [SKIP] Kön verifierat som '{gender_val}', inte 'Female'.")
                        cur.execute("UPDATE models SET completed = 1 WHERE name = ?", (model_name,))
                        db_conn.commit()
                        db_conn.close()
                        return
                    else:
                        if self.images_per_person > 0: # Only log OK in verbose or if needed
                             xprint(f"  [{model_name}] [GENDER OK] {gender_val}")
                else:
                    xprint(f"  [{model_name}] [VARNING] Hittade inget fält för kön. Fortsätter med försiktighet.")
            except Exception as ge:
                xprint(f"  [{model_name}] [VARNING] Kunde inte kontrollera kön: {ge}")

            await self.scroll_to_load_more(page, GALLERY_SELECTOR, 15, label=model_name)
        except Exception as e:
            xprint(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")
            if "404 Not Found" in str(e):
                cur.execute("UPDATE models SET failed_attempts = failed_attempts + 10 WHERE name = ?", (model_name,))
            else:
                cur.execute("UPDATE models SET failed_attempts = failed_attempts + 1 WHERE name = ?", (model_name,))
            db_conn.commit()
            db_conn.close()
            return

        links = await page.locator(GALLERY_SELECTOR).element_handles()
        for link in links:
            if get_local_image_count() >= self.images_per_person:
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
            if get_local_image_count() >= self.images_per_person:
                break
            xprint(f" [{model_name}] -> Öppnar galleri: {g_url}")
            try:
                await self.safe_goto(page, g_url, wait_for_selector="img", timeout=45000, label=model_name)
                await asyncio.sleep(1)
            except Exception as e:
                xprint(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")
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
                if not filename or not filename.endswith(".jpg"): continue
                is_highres = "/460/" not in u
                if filename not in best_images or (is_highres and "/460/" in best_images[filename]):
                    best_images[filename] = u
            for i_url in best_images.values():
                target_url = i_url
                if "/460/" in target_url: target_url = target_url.replace("/460/", "/1280/")
                status = await self.download_image(page, target_url, model_name, g_url)
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

    async def get_uncertain_models(self, report_file, min_samples=15):
        print("🔍 Samlar osäkra modeller baserat på rapport och Prolog...")
        flagged_names = []
        if not os.path.exists(report_file):
            print(f"⚠️ Rapportfil {report_file} saknas.")
            return []
        
        with open(report_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                # Kolla både Person A och Person B
                for p_key, s_key, v_key in [("Person A", "Samples A", "Intra Variance A"), ("Person B", "Samples B", "Intra Variance B")]:
                    name = row.get(p_key)
                    if not name: continue
                    samples = int(row.get(s_key, "0") or "0")
                    variance_str = row.get(v_key, "0.0")
                    variance = float(variance_str) if variance_str else 0.0
                    
                    # Fråga Prolog
                    decision = self.resolver.get_scrape_decision(name, samples, variance)
                    if decision["action"] in ["scrape", "mixed"]:
                        flagged_names.append({
                            "name": name,
                            "canonical": decision["canonical"],
                            "reason": decision["reason"]
                        })
        return flagged_names

async def main():
    import os
    try:
        total_cores = os.cpu_count()
        if total_cores and total_cores > 2:
            # Spara 2 kärnor till OS (ta bort de två sista kärnorna från affinity)
            allowed_cores = set(range(total_cores - 2))
            os.sched_setaffinity(0, allowed_cores)
            print(f"⚙️ CPU-Affinity satt till {len(allowed_cores)}/{total_cores} kärnor (sparar 2 till OS).")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Unified PornPics Scraper")
    parser.add_argument("--mode", choices=["tag", "report", "manual"], default="report", help="Scraping mode")
    parser.add_argument("--url", help="Start URL or alias (innie, pussy, closeup)")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--library", default=str(DEFAULT_LIBRARY), help=f"Main library directory to check for existing people (standard: {DEFAULT_LIBRARY})")
    parser.add_argument("--report", default="temp_uncertainty_report.csv", help="Uncertainty report CSV")
    parser.add_argument("--person", help="Manual person name(s), comma separated")
    parser.add_argument("--names-file", help="File with person names to scrape (one per line)")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent models")
    parser.add_argument("--images-per-person", type=int, default=50, help="Max images per person")
    parser.add_argument("--persons-per-run", type=int, default=20, help="Max persons to process")
    parser.add_argument("--wipe-db", action="store_true", help="Clear state DB")
    parser.add_argument("--scorched-earth", action="store_true", help="Abort and wipe gallery if multiple females are detected in an image")
    parser.add_argument("--re-scrape", action="store_true", help="Reset gallery and model status in DB for selected models to force a full re-scrape")
    args = parser.parse_args()

    # Bestäm output-mapp
    output_dir = Path(args.output) if args.output else Path("/home/marqs/Bilder/Nya")
    if args.url and args.url.lower() == "innie" and not args.output:
        output_dir = Path("/home/marqs/Bilder/Innie")
    
    library_dir = Path(args.library)

    scraper = PornPicsScraper(
        output_dir, 
        DEFAULT_DB_PATH, 
        args.concurrency, 
        args.images_per_person, 
        library_dir=library_dir,
        scorched_earth=args.scorched_earth
    )

    
    if args.wipe_db:
        print("🧹 Rensar databasen...")
        conn = scraper.get_db()
        conn.execute("DELETE FROM models")
        conn.execute("DELETE FROM galleries")
        conn.execute("DELETE FROM images")
        conn.commit()
        conn.close()
        sys.exit(0)

    models_to_process = [] # Lista med (name, url, canonical)

    async with AsyncCamoufox(headless=True) as browser:
        if args.mode == "report":
            # Steg 1: Hämta från CSV + Prolog
            flagged = await scraper.get_uncertain_models(args.report)
            print(f"✅ Prolog flaggade {len(flagged)} modeller för åtgärd.")
            
            # Steg 2: Mappa namn till URL:er
            async with await browser.new_context() as context:
                await scraper.setup_resource_blocking(context, allow_images=False)
                page = await context.new_page()
                print("🌍 Laddar artistlista för att hitta adresser...")
                await scraper.safe_goto(page, "https://www.pornpics.com/pornstars/list/", label="MapNames")
                list_links = await page.evaluate('''() => {
                    const map = {};
                    for (let a of document.querySelectorAll("a[href*='/pornstars/']")) {
                        if(a.innerText) map[a.innerText.trim().toLowerCase()] = a.href;
                    }
                    return map;
                }''')
                await page.close()
            
            for item in flagged:
                name = item["name"]
                canonical = item["canonical"]
                
                # Hoppa över om redan hanterad (disk eller DB)
                if scraper.is_model_done(name, canonical, force_rescrape=args.re_scrape):
                    continue
                
                m_url = list_links.get(name.lower())
                if not m_url:
                    m_url = f"https://www.pornpics.com/pornstars/{name.lower().replace(' ', '-')}/"
                
                models_to_process.append((name, m_url, canonical))
                if len(models_to_process) >= args.persons_per_run: break
            
        elif args.mode == "manual":
            # Steg 1: Hämta namn från argument eller fil
            target_names = []
            if args.person:
                target_names.extend([n.strip() for n in args.person.split(",") if n.strip()])
            if args.names_file and os.path.exists(args.names_file):
                with open(args.names_file, "r", encoding="utf-8") as f:
                    target_names.extend([line.strip() for line in f if line.strip()])
            
            print(f"📖 Läste {len(target_names)} namn för manuell skrapning.")
            
            # Steg 2: Mappa namn till URL:er (vi behöver artististan för detta)
            async with await browser.new_context() as context:
                await scraper.setup_resource_blocking(context, allow_images=False)
                page = await context.new_page()
                print("🌍 Laddar artistlista för att hitta adresser...")
                await scraper.safe_goto(page, "https://www.pornpics.com/pornstars/list/", label="MapNames")
                list_links = await page.evaluate('''() => {
                    const map = {};
                    for (let a of document.querySelectorAll("a[href*='/pornstars/']")) {
                        if(a.innerText) map[a.innerText.trim().toLowerCase()] = a.href;
                    }
                    return map;
                }''')
                await page.close()
            
            for name in target_names:
                # Resolve med Prolog
                decision = scraper.resolver.get_scrape_decision(name, 0, 0.0)
                canonical = decision["canonical"]
                
                # Kolla om redan hanterad
                if scraper.is_model_done(name, canonical, force_rescrape=args.re_scrape):
                    print(f"    [SKIP] {name} -> {canonical} är redan hanterad.")
                    continue

                m_url = list_links.get(name.lower())
                if not m_url:
                    m_url = f"https://www.pornpics.com/pornstars/{name.lower().replace(' ', '-')}/"
                
                models_to_process.append((name, m_url, canonical))
                if len(models_to_process) >= args.persons_per_run: break

        elif args.mode == "tag":
            # Steg 1: Hitta modeller via tag-sida
            start_url = TAG_ALIASES.get(args.url.lower(), args.url) if args.url else TAG_ALIASES["innie"]
            print(f"🔍 Letar modeller på: {start_url}")
            
            page = await browser.new_page()
            visited_galleries = set()
            processed_in_loop = set()
            
            try:
                await scraper.safe_goto(page, start_url, wait_for_selector="a[href*='/galleries/']", label="Discovery")
                while len(models_to_process) < args.persons_per_run:
                    gallery_links = await page.locator("a[href*='/galleries/']").element_handles()
                    for g_link in gallery_links:
                        if len(models_to_process) >= args.persons_per_run: break
                        g_href = await g_link.get_attribute("href")
                        if not g_href or g_href in visited_galleries: continue
                        visited_galleries.add(g_href)
                        
                        g_page = await browser.new_page()
                        try:
                            await scraper.safe_goto(g_page, urljoin(start_url, g_href), wait_for_selector=".gallery-info__content", label="Extraction")
                            model_links = await g_page.locator(".gallery-info__content a[href*='/pornstars/']").element_handles()
                            for m_link in model_links:
                                m_name = (await m_link.inner_text()).strip()
                                m_href = await m_link.get_attribute("href")
                                if not m_name or m_name in processed_in_loop: continue
                                processed_in_loop.add(m_name)
                                
                                # Resolve med Prolog innan vi checkar existens!
                                decision = scraper.resolver.get_scrape_decision(m_name, 0, 0.0) # 0,0.0 för okända
                                canonical = decision["canonical"]
                                
                                # Kolla om mappen finns i output, huvudbibliotek eller är markerad som klar i DB
                                if not scraper.is_model_done(m_name, canonical, force_rescrape=args.re_scrape):
                                    models_to_process.append((m_name, urljoin(start_url, m_href), canonical))
                                    print(f"    [FUNNEN] {m_name} -> {canonical} (NY) ({len(models_to_process)}/{args.persons_per_run})")
                                if len(models_to_process) >= args.persons_per_run: break
                        finally:
                            await g_page.close()
                    
                    if len(models_to_process) < args.persons_per_run:
                        # Scrolla för mer
                        await scraper.scroll_to_load_more(page, "a[href*='/galleries/']", len(gallery_links) + 12, label="Discovery")
            finally:
                await page.close()

        # Steg 3: Kör skrapningen
        if not models_to_process:
            print("🚀 Inga nya eller osäkra modeller hittades.")
            return

        models_with_fa = []
        for n, u, c in models_to_process:
            fa = scraper.get_failed_attempts(n, c)
            if fa >= 3:
                print(f"  [SKIP] Hoppar över {n} då den misslyckats {fa} gånger tidigare.")
                continue
            models_with_fa.append((fa, n, u, c))
        
        models_with_fa.sort(key=lambda x: x[0])
        models_to_process = [(n, u, c) for fa, n, u, c in models_with_fa]

        if args.re_scrape:
            db = scraper.get_db()
            cur = db.cursor()
            for n, u, c in models_to_process:
                cur.execute("UPDATE models SET completed = 0, started = 0 WHERE name = ? OR name = ?", (n, c))
                cur.execute("UPDATE galleries SET processed = 0 WHERE model_name = ? OR model_name = ?", (n, c))
            db.commit()
            db.close()
            print(f"🔄 Återställde databasstatus för {len(models_to_process)} utvalda modeller (--re-scrape).")

        print(f"🔄 Bearbetar {len(models_to_process)} modeller med concurrency={args.concurrency}")
        
        global UI
        UI = ScraperUI(args.concurrency, len(models_to_process))

        models_queue = asyncio.Queue()
        for c in models_to_process:
            models_queue.put_nowait(c)

        async def worker(idx):
            while True:
                if UI and UI.completed_models >= len(models_to_process):
                    UI.update_worker(idx, "-", "Uppnått mål!")
                    break
                
                try:
                    name, url, canonical = models_queue.get_nowait()
                except asyncio.QueueEmpty:
                    UI.update_worker(idx, "-", "Inga fler modeller!")
                    break

                delay = random.uniform(2, 6)
                if UI: UI.update_worker(idx, canonical, f"Väntar {delay:.1f}s...")
                await asyncio.sleep(delay)
                
                async with await browser.new_context() as context:
                    await scraper.setup_resource_blocking(context, allow_images=True)
                    w_page = await context.new_page()
                    try:
                        if UI: UI.update_worker(idx, canonical, "Skrapar...")
                        await scraper.scrape_model_galleries(w_page, canonical, url)
                        if UI: UI.update_worker(idx, canonical, "Klar!")
                    except Exception as e:
                        if UI: UI.update_worker(idx, canonical, f"Fel: {e}")
                    finally:
                        await w_page.close()
                models_queue.task_done()

        tasks = [worker(i) for i in range(args.concurrency)]
        
        with Live(UI.render(), refresh_per_second=4, screen=False) as live:
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
