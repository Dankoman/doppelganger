import sys
import re

with open("/home/marqs/Programmering/Python/3.11/doppelganger/tools/scrape_pornpics.py", "r") as f:
    content = f.read()

# Add rich imports
imports = """
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.text import Text
from rich.align import Align
"""
content = re.sub(r'from camoufox\.async_api import AsyncCamoufox', r'from camoufox.async_api import AsyncCamoufox\n' + imports, content)

# Add ScraperUI and UI
ui_code = """
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

        stats_text = Text(f"Klara: {self.completed_models}\\nTotalt: {self.total_models}\\nBilder: {self.total_images}\\n\\nQ: Ctrl+C för att avbryta", style="dim")
        self.layout["stats"].update(Panel(stats_text, title="Statistik"))

        log_content = "\\n".join(self.logs)
        self.layout["footer"].update(Panel(log_content, title="Senaste Händelser", border_style="white"))

        return self.layout

UI = None
"""
content = re.sub(r'class PornPicsScraper:', ui_code + '\nclass PornPicsScraper:', content)

# Modify methods to accept worker_idx and use UI
content = content.replace('def download_image(self, page, url, model_name, gallery_url):', 'def download_image(self, page, url, model_name, gallery_url, worker_idx=0):')
content = content.replace('def scrape_model_galleries(self, page, model_name, model_url):', 'def scrape_model_galleries(self, page, model_name, model_url, worker_idx=0):')

# print() replacements for `PornPicsScraper` using UI if available
content = content.replace('print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")', 'if UI: UI.log(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")\n                    else: print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")')
content = content.replace('if label: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")', 'if label:\n                        if UI: UI.log(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")\n                        else: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")')
content = content.replace('if label and i % 5 == 0:\n                print(f"  [{label}] Scrollar för mer innehåll... ({count}/{target_count})")', 'if label and i % 5 == 0:\n                pass')
content = content.replace('print(f"  [API VÄNTAR]', 'if UI: UI.log(f"  [API VÄNTAR]'); content = content.replace('print(f"  [API FEL]', 'if UI: UI.log(f"  [API FEL]')

# update worker
content = content.replace('print(f"  [{model_name}] Laddar ner: {url}")', 'if UI: UI.update_worker(worker_idx, model_name, f"Laddar ner: {url[:40]}...")')
content = content.replace('print(f"  [{model_name}] [SPARAD] {local_path}")', 'if UI:\n                UI.total_images += 1\n                UI.log(f"  [{model_name}] [SPARAD] {local_path.name}")\n            else:\n                print(f"  [{model_name}] [SPARAD] {local_path}")')
content = content.replace('print(f"  [{model_name}] [ERROR] {url}: {e}")', 'if UI: UI.log(f"  [{model_name}] [ERROR] {url}: {e}")\n            else: print(f"  [{model_name}] [ERROR] {url}: {e}")')
content = content.replace('print(f"[{model_name}] -> Letar gallerier på {model_url}")', 'if UI:\n            UI.log(f"[{model_name}] -> Letar gallerier på {model_url}")\n            UI.update_worker(worker_idx, model_name, "Laddar modellsida...")\n        else:\n            print(f"[{model_name}] -> Letar gallerier på {model_url}")')
content = content.replace('print(f"  [{model_name}] [SKIP] Kön verifierat som', 'if UI:\n                            UI.log(f"  [{model_name}] [SKIP] Kön verifierat som'); content = content.replace("UI.log(f\"  [{model_name}] [SKIP] Kön verifierat som '{gender_val}', inte 'Female'.\")", "UI.log(f\"  [{model_name}] [SKIP] Kön verifierat som '{gender_val}', inte 'Female'.\")\n                            UI.completed_models += 1\n                            UI.update_worker(worker_idx, '-', 'Klar (Skippad)!')");
content = content.replace('print(f"  [{model_name}] [GENDER OK] {gender_val}")', 'if UI: UI.log(f"  [{model_name}] [GENDER OK] {gender_val}")')
content = content.replace('print(f"  [{model_name}] [VARNING] Hittade inget', 'if UI: UI.log(f"  [{model_name}] [VARNING] Hittade inget')
content = content.replace('print(f"  [{model_name}] [VARNING] Kunde inte', 'if UI: UI.log(f"  [{model_name}] [VARNING] Kunde inte')
content = content.replace('print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")', 'if UI: UI.log(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")\n            else: print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")')
content = content.replace('print(f" [{model_name}] -> Öppnar galleri: {g_url}")', 'if UI: UI.update_worker(worker_idx, model_name, f"Öppnar galleri: {g_url[:40]}...")')
content = content.replace('print(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")', 'if UI: UI.log(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")')
content = content.replace('self.download_image(page, target_url, model_name, g_url)', 'self.download_image(page, target_url, model_name, g_url, worker_idx=worker_idx)')
content = content.replace('print(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")', 'if UI: UI.log(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")\n                    else: print(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")')
content = content.replace('print(f"[{model_name}] Färdig med modell!")', 'if UI:\n            UI.completed_models += 1\n            UI.update_worker(worker_idx, "-", "Klar!")\n            UI.log(f"[{model_name}] Färdig med modell!")\n        else:\n            print(f"[{model_name}] Färdig med modell!")')

# Replace the end part of main
worker_pool_code = """
        global UI
        target_count = len(models_to_process)
        UI = ScraperUI(args.concurrency, target_count)
        
        models_queue = asyncio.Queue()
        for c in models_to_process:
            models_queue.put_nowait(c)

        async def worker(idx):
            while True:
                if UI and UI.completed_models >= target_count:
                    UI.update_worker(idx, "-", "Uppnått mål!")
                    break
                
                try:
                    name, url, canonical = models_queue.get_nowait()
                except asyncio.QueueEmpty:
                    UI.update_worker(idx, "-", "Inga fler modeller!")
                    break

                delay = random.uniform(2, 6)
                if UI: UI.update_worker(idx, name, f"Väntar {delay:.1f}s...")
                await asyncio.sleep(delay)
                async with await browser.new_context() as context:
                    await scraper.setup_resource_blocking(context, allow_images=True)
                    w_page = await context.new_page()
                    try:
                        await scraper.scrape_model_galleries(w_page, canonical, url, worker_idx=idx)
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
"""
main_end_match = r'async def worker\(name, url, canonical\):.*await asyncio\.gather\(\*tasks\)'
content = re.sub(main_end_match, worker_pool_code.strip(), content, flags=re.DOTALL)

# Delete semaphore = asyncio.Semaphore(args.concurrency) line since it's unused now
content = content.replace("semaphore = asyncio.Semaphore(args.concurrency)", "")

with open("/home/marqs/Programmering/Python/3.11/doppelganger/tools/scrape_pornpics_new.py", "w") as f:
    f.write(content)
