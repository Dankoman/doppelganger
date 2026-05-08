import sys

with open("/home/marqs/Programmering/Python/3.11/doppelganger/tools/scrape_pornpics.py", "r") as f:
    content = f.read()

# Make changes to methods signatures
content = content.replace('def download_image(self, page, url, model_name, gallery_url):', 'def download_image(self, page, url, model_name, gallery_url, worker_idx=0):')
content = content.replace('def scrape_model_galleries(self, page, model_name, model_url):', 'def scrape_model_galleries(self, page, model_name, model_url, worker_idx=0):')

# print() -> UI.log()
content = content.replace('print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")', 'if UI: UI.log(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")\n                    else: print(f"  [{label}] [RETRY {attempt+1}] Misslyckades att ladda {url}: {msg}")')
content = content.replace('if label: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")', 'if label:\n                        if UI: UI.log(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")\n                        else: print(f"  [{label}] Stagnation vid {count} element. Avbryter scroll.")')
content = content.replace('if label and i % 5 == 0:\n                print(f"  [{label}] Scrollar för mer innehåll... ({count}/{target_count})")', 'if label and i % 5 == 0:\n                pass')
content = content.replace('print(f"  [API VÄNTAR] Servertjänsten är inte tillgänglig (omladdning pågår?). Försök {attempt+1}/{max_retries}...")', 'if UI: UI.log(f"  [API VÄNTAR] Servertjänsten är inte tillgänglig (omladdning pågår?). Försök {attempt+1}/{max_retries}...")\n                    else: print(f"  [API VÄNTAR] Servertjänsten är inte tillgänglig (omladdning pågår?). Försök {attempt+1}/{max_retries}...")')
content = content.replace('print(f"  [API FEL] Kunde inte nå servertjänsten efter {max_retries} försök.")', 'if UI: UI.log(f"  [API FEL] Kunde inte nå servertjänsten efter {max_retries} försök.")\n                    else: print(f"  [API FEL] Kunde inte nå servertjänsten efter {max_retries} försök.")')
content = content.replace('print(f"  [API FEL] Oväntat fel vid validering: {e}")', 'if UI: UI.log(f"  [API FEL] Oväntat fel vid validering: {e}")\n                else: print(f"  [API FEL] Oväntat fel vid validering: {e}")')

content = content.replace('print(f"  [{model_name}] Laddar ner: {url}")', 'if UI: UI.update_worker(worker_idx, model_name, f"Laddar ner: {url[:40]}...")')
content = content.replace('print(f"  [{model_name}] [SPARAD] {local_path}")', 'if UI:\n                UI.total_images += 1\n                UI.log(f"  [{model_name}] [SPARAD] {local_path.name}")\n            else:\n                print(f"  [{model_name}] [SPARAD] {local_path}")')
content = content.replace('print(f"  [{model_name}] [ERROR] {url}: {e}")', 'if UI: UI.log(f"  [{model_name}] [ERROR] {url}: {e}")\n            else: print(f"  [{model_name}] [ERROR] {url}: {e}")')

content = content.replace('print(f"[{model_name}] -> Letar gallerier på {model_url}")', 'if UI:\n            UI.log(f"[{model_name}] -> Letar gallerier på {model_url}")\n            UI.update_worker(worker_idx, model_name, "Laddar modellsida...")\n        else:\n            print(f"[{model_name}] -> Letar gallerier på {model_url}")')
content = content.replace('print(f"  [{model_name}] [SKIP] Kön verifierat som \'{gender_val}\', inte \'Female\'.")', 'if UI:\n                            UI.log(f"  [{model_name}] [SKIP] Kön verifierat som \'{gender_val}\', inte \'Female\'.")\n                            UI.completed_models += 1\n                            UI.update_worker(worker_idx, "-", "Klar (Skippad)!")\n                        else:\n                            print(f"  [{model_name}] [SKIP] Kön verifierat som \'{gender_val}\', inte \'Female\'.")')

content = content.replace('print(f"  [{model_name}] [GENDER OK] {gender_val}")', 'if UI: UI.log(f"  [{model_name}] [GENDER OK] {gender_val}")\n                             else: print(f"  [{model_name}] [GENDER OK] {gender_val}")')
content = content.replace('print(f"  [{model_name}] [VARNING] Hittade inget fält för kön. Fortsätter med försiktighet.")', 'if UI: UI.log(f"  [{model_name}] [VARNING] Hittade inget fält för kön. Fortsätter med försiktighet.")\n                    else: print(f"  [{model_name}] [VARNING] Hittade inget fält för kön. Fortsätter med försiktighet.")')
content = content.replace('print(f"  [{model_name}] [VARNING] Kunde inte kontrollera kön: {ge}")', 'if UI: UI.log(f"  [{model_name}] [VARNING] Kunde inte kontrollera kön: {ge}")\n                else: print(f"  [{model_name}] [VARNING] Kunde inte kontrollera kön: {ge}")')
content = content.replace('print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")', 'if UI: UI.log(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")\n            else: print(f"  [{model_name}] [FEL] Kunde inte ladda modellsida: {e}")')
content = content.replace('print(f" [{model_name}] -> Öppnar galleri: {g_url}")', 'if UI: UI.update_worker(worker_idx, model_name, f"Öppnar galleri: {g_url[:40]}...")\n            else: print(f" [{model_name}] -> Öppnar galleri: {g_url}")')
content = content.replace('print(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")', 'if UI: UI.log(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")\n                else: print(f"  [{model_name}] [SKIP] Kunde inte öppna galleri: {e}")')
content = content.replace('self.download_image(page, target_url, model_name, g_url)', 'self.download_image(page, target_url, model_name, g_url, worker_idx=worker_idx)')
content = content.replace('print(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")', 'if UI: UI.log(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")\n                    else: print(f"  [{model_name}] [SCORCHED EARTH] Multi-kvinna detekterad!")')
content = content.replace('print(f"[{model_name}] Färdig med modell!")', 'if UI:\n            UI.completed_models += 1\n            UI.update_worker(worker_idx, "-", "Klar!")\n            UI.log(f"[{model_name}] Färdig med modell!")\n        else:\n            print(f"[{model_name}] Färdig med modell!")')

with open("/home/marqs/Programmering/Python/3.11/doppelganger/tools/scrape_pornpics.py", "w") as f:
    f.write(content)

