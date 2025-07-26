#!/bin/bash

# Camoufox Installation Script med Virtual Environment Support
# Löser "externally-managed-environment" problemet

set -e

echo "🦊 Camoufox Installation med Virtual Environment"
echo "=============================================="

# Kontrollera att vi är i rätt mapp
if [ ! -f "requirements-camoufox-local.txt" ]; then
    echo "❌ requirements-camoufox-local.txt hittades inte"
    echo "💡 Kontrollera att du är i doppelganger-mappen och att patch är applicerad"
    exit 1
fi

# Kontrollera Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "🐍 Python version: $python_version"

# Kontrollera om virtual environment redan finns
if [ -d "camoufox-env" ]; then
    echo "📁 Virtual environment 'camoufox-env' finns redan"
    read -p "🤔 Vill du återskapa det? (y/N): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        echo "🗑️ Tar bort befintligt virtual environment..."
        rm -rf camoufox-env
    fi
fi

# Skapa virtual environment om det inte finns
if [ ! -d "camoufox-env" ]; then
    echo "📦 Skapar virtual environment..."
    python3 -m venv camoufox-env
    
    if [ ! -d "camoufox-env" ]; then
        echo "❌ Kunde inte skapa virtual environment"
        echo "💡 Försök installera python3-venv: sudo apt install python3-venv"
        exit 1
    fi
fi

# Aktivera virtual environment
echo "🔄 Aktiverar virtual environment..."
source camoufox-env/bin/activate

# Kontrollera att vi är i virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment kunde inte aktiveras"
    exit 1
fi

echo "✅ Virtual environment aktiverat: $VIRTUAL_ENV"

# Uppgradera pip
echo "⬆️ Uppgraderar pip..."
pip install --upgrade pip

# Installera Camoufox dependencies
echo "🦊 Installerar Camoufox dependencies..."
pip install -r requirements-camoufox-local.txt

# Ladda ner Camoufox browser
echo "⬇️ Laddar ner Camoufox browser..."
python -m camoufox fetch

# Verifiera installation
echo "✅ Verifierar installation..."
if python -c "import camoufox; print('Camoufox version:', camoufox.__version__)" 2>/dev/null; then
    echo "✅ Camoufox installerat framgångsrikt!"
else
    echo "❌ Camoufox installation misslyckades"
    exit 1
fi

# Visa Camoufox path
echo "📍 Camoufox browser path:"
python -m camoufox path

# Skapa aktiveringsscript för framtida användning
echo "📝 Skapar aktiveringsscript..."
cat > activate_camoufox.sh << 'EOF'
#!/bin/bash
echo "🦊 Aktiverar Camoufox virtual environment..."
source camoufox-env/bin/activate
echo "✅ Virtual environment aktiverat"
echo "💡 Kör 'deactivate' för att avsluta virtual environment"
echo "🕷️ Kör 'scrapy crawl your_spider' för att starta scraping"
EOF

chmod +x activate_camoufox.sh

# Skapa test-script
echo "🧪 Skapar test-script..."
cat > test_camoufox_venv.py << 'EOF'
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
EOF

chmod +x test_camoufox_venv.py

echo ""
echo "🎉 Camoufox installation klar!"
echo ""
echo "📋 Nästa steg:"
echo "   1. Testa installationen:"
echo "      python test_camoufox_venv.py"
echo ""
echo "   2. Kör Scrapy (virtual environment är redan aktiverat):"
echo "      scrapy crawl your_spider -s CLOSESPIDER_ITEMCOUNT=1"
echo ""
echo "   3. För framtida användning:"
echo "      ./activate_camoufox.sh"
echo "      scrapy crawl your_spider"
echo "      deactivate"
echo ""
echo "💡 Tips:"
echo "   - Virtual environment: $(pwd)/camoufox-env"
echo "   - Aktiveringsscript: ./activate_camoufox.sh"
echo "   - Test-script: ./test_camoufox_venv.py"
echo "   - För att avsluta: deactivate"
