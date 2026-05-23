import argparse
import os
from pathlib import Path
from PIL import Image
import imagehash
import time

def find_and_remove_duplicates(base_dir, delete_mode=False, hash_size=8, threshold=0):
    base_path = Path(base_dir)
    
    if not base_path.exists() or not base_path.is_dir():
        print(f"Fel: Katalogen {base_dir} existerar inte.")
        return

    # Giltiga bildformat (små bokstäver)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    
    # Statistik
    total_duplicates_found = 0
    total_bytes_saved = 0
    
    # os.walk går igenom mappen och alla undermappar
    for root, dirs, files in os.walk(base_path):
        current_dir = Path(root)
        
        # Samla alla bilder i den här specifika undermappen
        images_in_dir = [f for f in files if Path(f).suffix.lower() in valid_extensions]
        
        if not images_in_dir:
            continue
            
        print(f"\nSkannar mapp: {current_dir} ({len(images_in_dir)} bilder)")
        
        # Lista för att hålla reda på hashvärden i just denna mapp
        # Lista för att hålla reda på hashvärden i just denna mapp
        # Format: [(hash_objekt, filens_sökväg, upplösning), ...]
        hashes_in_dir = [] 
        duplicates_in_this_dir = []
        
        for filename in images_in_dir:
            filepath = current_dir / filename
            
            try:
                # Öppna bild och beräkna perceptuell hash (pHash)
                with Image.open(filepath) as img:
                    # phash är bra för att hitta bilder som är nedskalade eller har ändrad färg
                    img_hash = imagehash.phash(img, hash_size=hash_size)
                    img_res = img.width * img.height
                    
                is_duplicate = False
                # Jämför mot alla bilder vi redan sett i denna mapp
                for i, (existing_hash, existing_filepath, existing_res) in enumerate(hashes_in_dir):
                    # Beräkna skillnaden (Hamming distance) mellan hashar
                    if img_hash - existing_hash <= threshold:
                        if img_res > existing_res:
                            # Den nya bilden har högre upplösning. Radera den gamla.
                            duplicates_in_this_dir.append((existing_filepath, filepath))
                            # Uppdatera referensen i listan till den nya (bättre) bilden
                            hashes_in_dir[i] = (img_hash, filepath, img_res)
                        else:
                            # Den befintliga bilden har högre eller samma upplösning. Radera den nya.
                            duplicates_in_this_dir.append((filepath, existing_filepath))
                            
                        is_duplicate = True
                        break # Har hittat en matchning, sluta jämföra och gå till nästa fil
                
                if not is_duplicate:
                    # Spara hash för framtida jämförelser i samma mapp
                    hashes_in_dir.append((img_hash, filepath, img_res))
                    
            except Exception as e:
                print(f"  [VARNING] Kunde inte läsa {filename}: {e}")
                
        # Hantera hittade dubbletter i den här mappen
        for dup, original in duplicates_in_this_dir:
            file_size = dup.stat().st_size
            total_bytes_saved += file_size
            total_duplicates_found += 1
            
            if delete_mode:
                try:
                    dup.unlink()
                    print(f"  [RADERAD] {dup.name} (dubblett av {original.name})")
                except Exception as e:
                    print(f"  [FEL] Kunde inte radera {dup.name}: {e}")
            else:
                print(f"  [HITTAD] {dup.name} är en dubblett av {original.name}")

    # Summering
    print("\n--- Sammanfattning ---")
    print(f"Totalt antal hittade dubbletter: {total_duplicates_found}")
    print(f"Potentiellt sparad plats: {total_bytes_saved / (1024*1024):.2f} MB")
    
    if not delete_mode and total_duplicates_found > 0:
        print("\nOBS: Detta var en 'dry run'. Inga filer har raderats.")
        print("Kör skriptet med flaggan --delete för att faktiskt ta bort filerna.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hitta och ta bort visuella bilddubbletter per mapp.")
    parser.add_argument("--dir", type=str, default="/home/marqs/Bilder/pBook",
                        help="Mappen som ska genomsökas (standard: /home/marqs/Bilder/pBook)")
    parser.add_argument("--delete", action="store_true",
                        help="Radera dubbletterna (om flaggan saknas görs bara en testkörning)")
    parser.add_argument("--threshold", type=int, default=0,
                        help="Toleransnivå (0 = exakt samma phash, högre siffra = tillåt större skillnad, t.ex. 2-5 för mer aggressiv sökning. Standard är 0)")
    
    args = parser.parse_args()
    
    print(f"Startar sökning efter dubbletter i: {args.dir}")
    if args.delete:
        print("VARNING: Filer KOMMER att raderas!")
        time.sleep(2) # Liten paus så man hinner avbryta om man råkat trycka enter för tidigt
        
    start_time = time.time()
    find_and_remove_duplicates(args.dir, delete_mode=args.delete, threshold=args.threshold)
    print(f"\nTid för sökning: {time.time() - start_time:.1f} sekunder")
