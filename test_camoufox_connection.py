#!/usr/bin/env python3
import time
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def test_camoufox_server():
    print("🔍 Testar Camoufox-server anslutning...")
    
    print("\n1️⃣ Testar HTTP status endpoint...")
    try:
        response = requests.get("http://camoufox-server:4444/wd/hub/status", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP status OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ HTTP status fel: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP anslutning misslyckades: {e}")
        return False
    
    print("\n2️⃣ Testar WebDriver session...")
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        print("   Skapar WebDriver session...")
        driver = webdriver.Remote(
            command_executor='http://camoufox-server:4444/wd/hub',
            options=options
        )
        
        driver.set_page_load_timeout(10)
        driver.implicitly_wait(5)
        
        print("✅ WebDriver session skapad")
        
        print("\n3️⃣ Testar sidladdning...")
        start_time = time.time()
        driver.get("https://httpbin.org/user-agent")
        load_time = time.time() - start_time
        
        print(f"✅ Sida laddad på {load_time:.2f}s")
        
        page_source = driver.page_source
        if "Mozilla" in page_source:
            print(f"✅ Innehåll hämtat ({len(page_source)} tecken)")
        else:
            print(f"⚠️ Oväntat innehåll ({len(page_source)} tecken)")
        
        return True
        
    except Exception as e:
        print(f"❌ WebDriver test fel: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
                print("🔒 WebDriver session stängd")
            except:
                pass

if __name__ == "__main__":
    success = test_camoufox_server()
    exit(0 if success else 1)
