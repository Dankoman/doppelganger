#!/bin/bash

# Fix för syntax-fel i run_scraper.sh
echo "🔧 Fixar syntax-fel i run_scraper.sh..."

# Kontrollera att vi är i rätt katalog
if [ ! -f "run_scraper.sh" ]; then
    echo "❌ Fel: run_scraper.sh inte hittad. Kör detta script från doppelganger root-katalogen"
    exit 1
fi

# Backup befintlig fil
cp run_scraper.sh run_scraper.sh.backup.syntax.$(date +%Y%m%d_%H%M%S)
echo "📦 Backup skapad: run_scraper.sh.backup.syntax.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Ersätter run_scraper.sh med fixad version..."

# Ersätt med fixad version
cat > run_scraper.sh << 'EOF'
#!/bin/bash

# Doppelganger Scraper - Enhanced Anti-Blocking Edition with Chrome Headless + Camoufox
# Hanteringsscript för Docker-baserad scraping

set -e

# Färger för output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                      🕷️  Doppelganger Scraper v2.0                          ║"
    echo "║         Enhanced Anti-Blocking + Chrome Headless + Camoufox Edition         ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Kontrollera att Docker körs
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker körs inte. Starta Docker först.${NC}"
        exit 1
    fi
}

# Skapa nödvändiga kataloger
ensure_directories() {
    mkdir -p images crawls logs httpcache
    chmod 755 images crawls logs httpcache
}

# Camoufox-specifika funktioner
camoufox_test() {
    echo -e "${PURPLE}🦊 Testar Camoufox-integration...${NC}"
    echo -e "${YELLOW}🔍 Startar Camoufox-server...${NC}"
    
    # Starta Camoufox-server först
    docker-compose up -d camoufox-server
    
    # Vänta på att servern startar
    echo -e "${YELLOW}⏳ Väntar på att Camoufox-server startar...${NC}"
    sleep 10
    
    # Kontrollera att servern svarar
    if docker-compose exec camoufox-server curl -s http://localhost:4444/wd/hub/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Camoufox-server är redo${NC}"
    else
        echo -e "${YELLOW}⚠️ Camoufox-server svarar inte, fortsätter ändå...${NC}"
    fi
    
    echo -e "${BLUE}🧪 Testar scraping med Camoufox (1 profil)...${NC}"
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=INFO \
        -s DOWNLOAD_DELAY=10
}

camoufox_sample() {
    echo -e "${PURPLE}🦊 Scrapar 10 profiler med Camoufox...${NC}"
    
    # Starta Camoufox-server
    docker-compose up -d camoufox-server
    sleep 5
    
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=10 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=INFO \
        -s DOWNLOAD_DELAY=8
}

camoufox_run() {
    echo -e "${PURPLE}🦊 Scrapar alla profiler med Camoufox...${NC}"
    echo -e "${RED}⚠️ Detta kommer att ta mycket lång tid (6360 profiler)${NC}"
    read -p "Är du säker? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose up -d camoufox-server
        sleep 5
        
        docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
            -s CAMOUFOX_ENABLED=True \
            -s LOG_LEVEL=INFO \
            -s DOWNLOAD_DELAY=8
    else
        echo "Avbrutet."
    fi
}

camoufox_debug() {
    echo -e "${PURPLE}🦊 Debug-läge för Camoufox...${NC}"
    docker-compose up -d camoufox-server
    sleep 5
    
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=DEBUG \
        -s DOWNLOAD_DELAY=15 \
        -s CAMOUFOX_CLOUDFLARE_WAIT=20
}

camoufox_verify() {
    echo -e "${BLUE}🔍 Verifierar Camoufox-installation...${NC}"
    docker-compose up -d camoufox-server
    sleep 10
    
    echo -e "${YELLOW}🦊 Kontrollerar Camoufox-server...${NC}"
    if docker-compose exec camoufox-server curl -s http://localhost:4444/wd/hub/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Camoufox-server fungerar${NC}"
    else
        echo -e "${RED}❌ Camoufox-server svarar inte${NC}"
    fi
}

camoufox_stop() {
    echo -e "${YELLOW}🛑 Stoppar Camoufox-server...${NC}"
    docker-compose stop camoufox-server
    echo -e "${GREEN}✅ Camoufox-server stoppad${NC}"
}

camoufox_logs() {
    echo -e "${YELLOW}📋 Visar Camoufox-server loggar...${NC}"
    docker-compose logs camoufox-server
}

camoufox_connection_test() {
    echo -e "${BLUE}🔍 Testar Camoufox-server anslutning...${NC}"
    docker-compose up -d camoufox-server
    sleep 10
    
    echo -e "${YELLOW}🧪 Kör connection test...${NC}"
    docker-compose run --rm camoufox-scraper python3 test_camoufox_connection.py
}

camoufox_quick_test() {
    echo -e "${PURPLE}🦊 Snabb Camoufox-test (kortare timeouts)...${NC}"
    docker-compose up -d camoufox-server
    sleep 5
    
    docker-compose run --rm camoufox-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CAMOUFOX_ENABLED=True \
        -s LOG_LEVEL=DEBUG \
        -s DOWNLOAD_DELAY=5 \
        -s CAMOUFOX_PAGE_LOAD_TIMEOUT=10 \
        -s CAMOUFOX_WEBDRIVER_TIMEOUT=8
}

# URL-baserade scraper-funktioner
url_test() {
    show_banner
    echo -e "${YELLOW}🧪 Testar URL-baserad scraper med 5 profiler...${NC}"
    check_docker
    ensure_directories
    
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er i fil: $(wc -l < profile_urls.txt)${NC}"
    
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=5 \
        -s LOG_LEVEL=INFO
}

url_sample() {
    show_banner
    echo -e "${YELLOW}📊 Kör URL-baserad scraper för 100 profiler...${NC}"
    check_docker
    ensure_directories
    
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er i fil: $(wc -l < profile_urls.txt)${NC}"
    
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=100 \
        -s LOG_LEVEL=INFO
}

url_run() {
    show_banner
    echo -e "${YELLOW}🚀 Kör URL-baserad scraper för alla profiler...${NC}"
    check_docker
    ensure_directories
    
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er att scrapa: $(wc -l < profile_urls.txt)${NC}"
    echo -e "${YELLOW}⚠️  Detta kommer att scrapa ALLA profiler. Fortsätt? (y/N):${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
            -s LOG_LEVEL=INFO
    else
        echo -e "${CYAN}ℹ️  Scraping avbruten${NC}"
    fi
}

# Chrome Headless-funktioner
chrome_test() {
    show_banner
    echo -e "${YELLOW}🧪 Testar Chrome headless-integration...${NC}"
    check_docker
    
    echo -e "${CYAN}🚀 Testar Chrome-scraper med 1 profil...${NC}"
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s LOG_LEVEL=INFO \
        -s CHROME_ENABLED=True \
        -s DOWNLOAD_DELAY=8 \
        -s CONCURRENT_REQUESTS=1
}

chrome_sample() {
    show_banner
    echo -e "${YELLOW}📊 Kör Chrome-scraper för 10 profiler...${NC}"
    check_docker
    ensure_directories
    
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kör först url_test för att sätta upp URL-listan.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er: $(wc -l < profile_urls.txt)${NC}"
    
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=10 \
        -s LOG_LEVEL=INFO \
        -s CHROME_ENABLED=True \
        -s DOWNLOAD_DELAY=8 \
        -s CONCURRENT_REQUESTS=1
}

# Hjälpfunktioner
show_help() {
    show_banner
    echo -e "${YELLOW}Användning:${NC} $0 [KOMMANDO]"
    echo ""
    echo -e "${CYAN}Tillgängliga kommandon:${NC}"
    echo ""
    echo -e "  ${GREEN}build${NC}           Bygg Docker-imagen med alla förbättringar"
    echo -e "  ${GREEN}test${NC}            Kör test med begränsad scraping (5 items)"
    echo -e "  ${GREEN}run${NC}             Kör full scraping (interaktivt)"
    echo -e "  ${GREEN}stop${NC}            Stoppa alla körande containers"
    echo -e "  ${GREEN}logs${NC}            Visa live loggar från scrapern"
    echo -e "  ${GREEN}shell${NC}           Öppna bash-shell i container"
    echo -e "  ${GREEN}status${NC}          Visa status för containers"
    echo -e "  ${GREEN}clean${NC}           Rensa alla containers och volymer"
    echo ""
    echo -e "${CYAN}URL-baserade kommandon:${NC}"
    echo -e "  ${GREEN}url_test${NC}       Testa URL-baserad scraper (5 profiler)"
    echo -e "  ${GREEN}url_sample${NC}     Scrapa 100 profiler från URL-lista"
    echo -e "  ${GREEN}url_run${NC}        Scrapa alla profiler från URL-lista"
    echo ""
    echo -e "${CYAN}Chrome Headless-kommandon:${NC}"
    echo -e "  ${GREEN}chrome_test${NC}     Testa Chrome headless-integration (1 profil)"
    echo -e "  ${GREEN}chrome_sample${NC}   Scrapa 10 profiler med Chrome headless"
    echo ""
    echo -e "${PURPLE}Camoufox-kommandon (kringgå Cloudflare):${NC}"
    echo "  camoufox_test     Testa Camoufox-integration (1 profil)"
    echo "  camoufox_sample   Scrapa 10 profiler med Camoufox"
    echo "  camoufox_run      Scrapa alla profiler med Camoufox"
    echo "  camoufox_debug    Debug Camoufox-scraper"
    echo "  camoufox_verify   Verifiera Camoufox-installation"
    echo "  camoufox_stop     Stoppa Camoufox-server"
    echo "  camoufox_logs     Visa Camoufox-server loggar"
    echo "  camoufox_connection_test  Testa Camoufox-server anslutning"
    echo "  camoufox_quick_test       Snabb test med kortare timeouts"
    echo ""
    echo -e "${YELLOW}Exempel:${NC}"
    echo -e "  $0 build && $0 camoufox_test     ${PURPLE}# Bygg och testa Camoufox${NC}"
    echo -e "  $0 camoufox_sample               ${PURPLE}# Scrapa 10 profiler med Camoufox${NC}"
    echo -e "  $0 url_test                      ${PURPLE}# Testa URL-scraper${NC}"
    echo -e "  $0 chrome_test                   ${PURPLE}# Testa Chrome headless${NC}"
    echo ""
}

# Huvudfunktioner
case "${1:-help}" in
    "build")
        show_banner
        echo -e "${YELLOW}🔨 Bygger Docker-imagen med Enhanced Anti-Blocking + Chrome + Camoufox...${NC}"
        check_docker
        ensure_directories
        
        docker-compose build --no-cache
        
        echo -e "${GREEN}✅ Docker-imagen byggd framgångsrikt!${NC}"
        echo -e "${CYAN}💡 Testa nu med: $0 camoufox_test${NC}"
        ;;
        
    "test")
        show_banner
        echo -e "${YELLOW}🧪 Kör test med begränsad scraping...${NC}"
        check_docker
        ensure_directories
        
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all \
            -s CLOSESPIDER_ITEMCOUNT=5 \
            -s DOWNLOAD_DELAY=5 \
            -s CONCURRENT_REQUESTS=1 \
            -L INFO
        ;;
        
    "run")
        show_banner
        echo -e "${YELLOW}🚀 Kör full scraping (interaktivt)...${NC}"
        check_docker
        ensure_directories
        
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all
        ;;
        
    "stop")
        show_banner
        echo -e "${YELLOW}🛑 Stoppar alla containers...${NC}"
        check_docker
        
        docker-compose down
        echo -e "${GREEN}✅ Alla containers stoppade${NC}"
        ;;
        
    "logs")
        show_banner
        echo -e "${YELLOW}📋 Visar live loggar (Ctrl+C för att avsluta)...${NC}"
        check_docker
        
        docker-compose logs -f doppelganger-scraper
        ;;
        
    "shell")
        show_banner
        echo -e "${YELLOW}🐚 Öppnar bash-shell i container...${NC}"
        check_docker
        
        docker-compose run --rm doppelganger-scraper bash
        ;;
        
    "status")
        show_banner
        echo -e "${YELLOW}📊 Container-status:${NC}"
        check_docker
        
        docker-compose ps
        ;;
        
    "clean")
        show_banner
        echo -e "${YELLOW}🧹 Rensar containers och volymer...${NC}"
        check_docker
        
        read -p "⚠️  Detta kommer att ta bort alla containers och data. Fortsätt? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker system prune -f
            echo -e "${GREEN}✅ Rensning klar${NC}"
        else
            echo -e "${CYAN}ℹ️  Rensning avbruten${NC}"
        fi
        ;;
        
    # URL-baserade kommandon
    "url_test")
        url_test
        ;;
    "url_sample")
        url_sample
        ;;
    "url_run")
        url_run
        ;;
        
    # Chrome Headless-kommandon
    "chrome_test")
        chrome_test
        ;;
    "chrome_sample")
        chrome_sample
        ;;
        
    # Camoufox-kommandon
    "camoufox_test")
        camoufox_test
        ;;
    "camoufox_sample")
        camoufox_sample
        ;;
    "camoufox_run")
        camoufox_run
        ;;
    "camoufox_debug")
        camoufox_debug
        ;;
    "camoufox_verify")
        camoufox_verify
        ;;
    "camoufox_stop")
        camoufox_stop
        ;;
    "camoufox_logs")
        camoufox_logs
        ;;
    "camoufox_connection_test")
        camoufox_connection_test
        ;;
    "camoufox_quick_test")
        camoufox_quick_test
        ;;
        
    "help"|*)
        show_help
        ;;
esac
EOF

# Gör scriptet körbart
chmod +x run_scraper.sh

echo ""
echo "🎉 Syntax-fel fixat!"
echo ""
echo "📋 Vad som fixats:"
echo "  ✅ Borttaget duplicerade funktioner"
echo "  ✅ Fixat ofullständiga funktioner"
echo "  ✅ Rensat case-statement struktur"
echo "  ✅ Lagt till alla Camoufox-kommandon"
echo ""
echo "🧪 Testa nu:"
echo "  ./run_scraper.sh build"
echo "  ./run_scraper.sh camoufox_test"

