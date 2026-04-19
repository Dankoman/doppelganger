#!/usr/bin/env python3
"""
Test script för Chrome headless-integration
Testar anslutning till chromedp/headless-shell Docker-instanser
"""

import requests
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_chrome_connection():
    """Testa anslutning till Chrome-instanser"""
    
    success_count = 0
    
    for port in [9222, 9223]:
        print(f"\n🔍 Testar Chrome på 192.168.0.50:{port}...")
        
        try:
            # Testa Chrome DevTools API
            response = requests.get(f"http://192.168.0.50:{port}/json/version", timeout=5)
            if response.status_code == 200:
                version_info = response.json()
                print(f"✅ Chrome DevTools API: {version_info.get('Browser', 'Unknown')}")
                print(f"   WebKit: {version_info.get('WebKit-Version', 'Unknown')}")
                
                # Testa WebDriver-anslutning
                options = Options()
                options.add_experimental_option("debuggerAddress", f"192.168.0.50:{port}")
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                
                driver = webdriver.Chrome(options=options)
                
                # Testa med en enkel sida
                driver.get("https://httpbin.org/user-agent")
                
                # Hämta user agent från sidan
                body_element = driver.find_element(By.TAG_NAME, 'body')
                body_text = body_element.text
                
                print(f"✅ WebDriver-anslutning fungerar")
                print(f"   Response: {body_text[:100]}...")
                
                # Testa med målsidan
                print(f"🎯 Testar målsida...")
                driver.get("https://www.mypornstarbook.net/")
                
                page_title = driver.title
                page_length = len(driver.page_source)
                
                print(f"   Titel: {page_title}")
                print(f"   Sidlängd: {page_length} bytes")
                
                if "403" in page_title or page_length < 1000:
                    print(f"⚠️  Möjlig blockering detekterad")
                else:
                    print(f"✅ Målsida laddad framgångsrikt")
                
                driver.quit()
                success_count += 1
                
            else:
                print(f"❌ Chrome DevTools API: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Anslutningsfel: {e}")
        except Exception as e:
            print(f"❌ WebDriver-fel: {e}")
    
    print(f"\n📊 Resultat: {success_count}/2 Chrome-instanser fungerar")
    
    if success_count == 0:
        print("\n🚨 Inga Chrome-instanser tillgängliga!")
        print("   Kontrollera att chromedp/headless-shell körs på:")
        print("   - 192.168.0.50:9222")
        print("   - 192.168.0.50:9223")
        return False
    elif success_count == 1:
        print("\n⚠️  Endast en Chrome-instans tillgänglig")
        print("   Scrapern kommer att fungera men utan load balancing")
        return True
    else:
        print("\n🎉 Alla Chrome-instanser fungerar perfekt!")
        print("   Redo för Chrome headless-scraping")
        return True

def test_chrome_scraping():
    """Testa Chrome-scraping med en profil-URL"""
    
    print(f"\n🧪 Testar Chrome-scraping...")
    
    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", "192.168.0.50:9222")
        options.add_argument('--no-sandbox')
        
        driver = webdriver.Chrome(options=options)
        
        # Testa med en profil-URL
        test_url = "https://www.mypornstarbook.net/pornstars/a/aali_kali/index.php"
        print(f"🎯 Testar URL: {test_url}")
        
        driver.get(test_url)
        
        # Vänta lite
        import time
        time.sleep(3)
        
        page_source = driver.page_source
        page_title = driver.title
        
        print(f"   Titel: {page_title}")
        print(f"   Sidlängd: {len(page_source)} bytes")
        
        # Kontrollera innehåll
        if "403" in page_title or "Forbidden" in page_source:
            print(f"❌ Profil blockerad")
            return False
        elif len(page_source) < 1000:
            print(f"❌ För lite innehåll")
            return False
        else:
            print(f"✅ Profil laddad framgångsrikt")
            
            # Leta efter bilder
            img_tags = driver.find_elements(By.TAG_NAME, 'img')
            print(f"   Hittade {len(img_tags)} img-taggar")
            
            return True
        
        driver.quit()
        
    except Exception as e:
        print(f"❌ Chrome-scraping fel: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Chrome Headless Integration Test")
    print("=" * 50)
    
    # Testa anslutning
    connection_ok = test_chrome_connection()
    
    if connection_ok:
        # Testa scraping
        scraping_ok = test_chrome_scraping()
        
        if scraping_ok:
            print(f"\n🎉 Alla tester godkända! Chrome headless-integration redo.")
            sys.exit(0)
        else:
            print(f"\n⚠️  Anslutning OK men scraping misslyckades")
            sys.exit(1)
    else:
        print(f"\n❌ Chrome-anslutning misslyckades")
        sys.exit(1)

