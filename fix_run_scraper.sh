#!/bin/bash

# Script för att lägga till Camoufox-kommandon i run_scraper.sh
echo "🔧 Fixar run_scraper.sh med Camoufox-kommandon..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "run_scraper.sh" ]; then
    echo "❌ Fel: run_scraper.sh inte hittad. Kör detta script från doppelganger root-katalogen"
    exit 1
fi

# Backup befintlig fil
cp run_scraper.sh run_scraper.sh.backup.camoufox.$(date +%Y%m%d_%H%M%S)
echo "📦 Backup skapad: run_scraper.sh.backup.camoufox.$(date +%Y%m%d_%H%M%S)"

# Lägg till Camoufox-funktioner före case-statement
echo "📝 Lägger till Camoufox-funktioner..."

# Hitta raden före case-statement och lägg till funktioner
sed -i '/^case "\${1:-help}" in$/i\
# Camoufox-specifika funktioner\
camoufox_test() {\
    echo -e "${PURPLE}🦊 Testar Camoufox-integration...${NC}"\
    echo -e "${YELLOW}🔍 Startar Camoufox-server...${NC}"\
    \
    # Starta Camoufox-server först\
    docker-compose up -d camoufox-server\
    \
    # Vänta på att servern startar\
    echo -e "${YELLOW}⏳ Väntar på att Camoufox-server startar...${NC}"\
    sleep 10\
    \
    # Kontrollera att servern svarar\
    if docker-compose exec camoufox-server curl -s http://localhost:4444/wd/hub/status > /dev/null 2>&1; then\
        echo -e "${GREEN}✅ Camoufox-server är redo${NC}"\
    else\
        echo -e "${YELLOW}⚠️ Camoufox-server svarar inte, fortsätter ändå...${NC}"\
    fi\
    \
    echo -e "${BLUE}🧪 Testar scraping med Camoufox (1 profil)...${NC}"\
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \\\
        -s CLOSESPIDER_ITEMCOUNT=1 \\\
        -s CAMOUFOX_ENABLED=True \\\
        -s LOG_LEVEL=INFO \\\
        -s DOWNLOAD_DELAY=10\
}\
\
camoufox_sample() {\
    echo -e "${PURPLE}🦊 Scrapar 10 profiler med Camoufox...${NC}"\
    \
    # Starta Camoufox-server\
    docker-compose up -d camoufox-server\
    sleep 5\
    \
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \\\
        -s CLOSESPIDER_ITEMCOUNT=10 \\\
        -s CAMOUFOX_ENABLED=True \\\
        -s LOG_LEVEL=INFO \\\
        -s DOWNLOAD_DELAY=8\
}\
\
camoufox_run() {\
    echo -e "${PURPLE}🦊 Scrapar alla profiler med Camoufox...${NC}"\
    echo -e "${RED}⚠️ Detta kommer att ta mycket lång tid (6360 profiler)${NC}"\
    read -p "Är du säker? (y/N): " -n 1 -r\
    echo\
    if [[ $REPLY =~ ^[Yy]$ ]]; then\
        docker-compose up -d camoufox-server\
        sleep 5\
        \
        docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \\\
            -s CAMOUFOX_ENABLED=True \\\
            -s LOG_LEVEL=INFO \\\
            -s DOWNLOAD_DELAY=8\
    else\
        echo "Avbrutet."\
    fi\
}\
\
camoufox_debug() {\
    echo -e "${PURPLE}🦊 Debug-läge för Camoufox...${NC}"\
    docker-compose up -d camoufox-server\
    sleep 5\
    \
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \\\
        -s CLOSESPIDER_ITEMCOUNT=1 \\\
        -s CAMOUFOX_ENABLED=True \\\
        -s LOG_LEVEL=DEBUG \\\
        -s DOWNLOAD_DELAY=15 \\\
        -s CAMOUFOX_CLOUDFLARE_WAIT=20\
}\
\
camoufox_verify() {\
    echo -e "${BLUE}🔍 Verifierar Camoufox-installation...${NC}"\
    docker-compose up -d camoufox-server\
    sleep 10\
    \
    echo -e "${YELLOW}🦊 Kontrollerar Camoufox-server...${NC}"\
    if docker-compose exec camoufox-server curl -s http://localhost:4444/wd/hub/status > /dev/null 2>&1; then\
        echo -e "${GREEN}✅ Camoufox-server fungerar${NC}"\
    else\
        echo -e "${RED}❌ Camoufox-server svarar inte${NC}"\
    fi\
}\
\
camoufox_stop() {\
    echo -e "${YELLOW}🛑 Stoppar Camoufox-server...${NC}"\
    docker-compose stop camoufox-server\
    echo -e "${GREEN}✅ Camoufox-server stoppad${NC}"\
}\
\
camoufox_logs() {\
    echo -e "${YELLOW}📋 Visar Camoufox-server loggar...${NC}"\
    docker-compose logs camoufox-server\
}\
' run_scraper.sh

# Lägg till Camoufox-kommandon i case-statement
echo "📝 Lägger till Camoufox-kommandon i case-statement..."

# Hitta raden före "help"|*) och lägg till Camoufox-kommandon
sed -i '/^    "help"|\*)/i\
    # Camoufox-kommandon\
    "camoufox_test")\
        camoufox_test\
        ;;\
    "camoufox_sample")\
        camoufox_sample\
        ;;\
    "camoufox_run")\
        camoufox_run\
        ;;\
    "camoufox_debug")\
        camoufox_debug\
        ;;\
    "camoufox_verify")\
        camoufox_verify\
        ;;\
    "camoufox_stop")\
        camoufox_stop\
        ;;\
    "camoufox_logs")\
        camoufox_logs\
        ;;' run_scraper.sh

# Uppdatera hjälp-texten
echo "📝 Uppdaterar hjälp-text med Camoufox-kommandon..."

# Hitta hjälp-sektionen och lägg till Camoufox-kommandon
sed -i '/Chrome Headless-kommandon/a\
\
        echo -e "${PURPLE}Camoufox-kommandon (kringgå Cloudflare):${NC}"\
        echo "  camoufox_test     Testa Camoufox-integration (1 profil)"\
        echo "  camoufox_sample   Scrapa 10 profiler med Camoufox"\
        echo "  camoufox_run      Scrapa alla profiler med Camoufox"\
        echo "  camoufox_debug    Debug Camoufox-scraper"\
        echo "  camoufox_verify   Verifiera Camoufox-installation"\
        echo "  camoufox_stop     Stoppa Camoufox-server"\
        echo "  camoufox_logs     Visa Camoufox-server loggar"' run_scraper.sh

# Uppdatera exempel-sektionen
sed -i '/chrome_sample        # Scrapa 10 profiler med Chrome/a\
        echo "  $0 camoufox_test          # Testa Camoufox med 1 profil"\
        echo "  $0 camoufox_sample        # Scrapa 10 profiler med Camoufox"' run_scraper.sh

# Uppdatera slutkommentaren
sed -i 's/Chrome headless-integration (ultimat bot-bypass)/Chrome headless + Camoufox-integration (ultimat bot-bypass)/' run_scraper.sh

echo ""
echo "🎉 run_scraper.sh uppdaterad med Camoufox-kommandon!"
echo ""
echo "📋 Nya kommandon tillgängliga:"
echo "  ./run_scraper.sh camoufox_test     # Testa med 1 profil"
echo "  ./run_scraper.sh camoufox_sample   # Scrapa 10 profiler"
echo "  ./run_scraper.sh camoufox_run      # Scrapa alla profiler"
echo "  ./run_scraper.sh camoufox_verify   # Verifiera installation"
echo ""
echo "🦊 Testa nu: ./run_scraper.sh camoufox_test"

