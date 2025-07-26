#!/usr/bin/env python3
"""
Test script för Camoufox i virtual environment
"""

import asyncio
import sys
import os

def check_virtual_env():
    """Kontrollera att vi är i virtual environment"""
    if 'VIRTUAL_ENV' not in os.environ:
        print("⚠️ Varning: Inte i virtual environment")
        print("💡 Kör: source camoufox-env/bin/activate")
        return False
    else:
        print(f"✅ Virtual environment: {os.environ['VIRTUAL_ENV']}")
        return True

async def test_camoufox():
    """Test av Camoufox"""
    print("🦊 Testar Camoufox...")
    
    try:
        from camoufox.async_api import AsyncCamoufox
        
        async with AsyncCamoufox(headless=True, geoip=True) as browser:
            print("✅ Camoufox browser startad")
            
            page = await browser.new_page()
            await page.goto("https://httpbin.org/user-agent")
            content = await page.content()
            
            if "Firefox" in content:
                print("✅ User agent verifierad (Firefox)")
                print(f"📄 Sida innehåll: {len(content)} tecken")
                return True
            else:
                print("⚠️ Oväntat user agent")
                return False
                
    except ImportError as e:
        print(f"❌ Import fel: {e}")
        print("💡 Kontrollera att virtual environment är aktiverat")
        return False
    except Exception as e:
        print(f"❌ Test misslyckades: {e}")
        return False

async def main():
    """Huvudfunktion"""
    print("🧪 Camoufox Virtual Environment Test")
    print("=" * 40)
    
    # Kontrollera virtual environment
    venv_ok = check_virtual_env()
    
    # Test Camoufox
    camoufox_ok = await test_camoufox()
    
    print("\n📊 Test Resultat:")
    print(f"   Virtual Environment: {'✅ OK' if venv_ok else '❌ FAIL'}")
    print(f"   Camoufox:           {'✅ OK' if camoufox_ok else '❌ FAIL'}")
    
    if venv_ok and camoufox_ok:
        print("\n🎉 Allt fungerar!")
        print("💡 Du kan nu köra: scrapy crawl your_spider")
        return True
    else:
        print("\n❌ Vissa tester misslyckades")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
