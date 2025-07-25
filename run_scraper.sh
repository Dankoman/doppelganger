#!/bin/bash

# Doppelganger Scraper - Enhanced Anti-Blocking Edition
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
    echo "║                    Enhanced Anti-Blocking Edition                            ║"
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

# URL-baserade scraper-funktioner
url_test() {
    show_banner
    echo -e "${YELLOW}🧪 Testar URL-baserad scraper med 5 profiler...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att URL-filen finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er i fil: $(wc -l < profile_urls.txt)${NC}"
    
    # Kör test med URL-baserad spider
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=5 \
        -s LOG_LEVEL=INFO
}

url_run() {
    show_banner
    echo -e "${YELLOW}🚀 Kör URL-baserad scraper för alla profiler...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att URL-filen finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er att scrapa: $(wc -l < profile_urls.txt)${NC}"
    echo -e "${YELLOW}⚠️  Detta kommer att scrapa ALLA profiler. Fortsätt? (y/N):${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Kör full URL-baserad scraping
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
            -s LOG_LEVEL=INFO
    else
        echo -e "${CYAN}ℹ️  Scraping avbruten${NC}"
    fi
}

url_sample() {
    show_banner
    echo -e "${YELLOW}📊 Kör URL-baserad scraper för 100 profiler...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att URL-filen finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er i fil: $(wc -l < profile_urls.txt)${NC}"
    
    # Kör sample med URL-baserad spider
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -s CLOSESPIDER_ITEMCOUNT=100 \
        -s LOG_LEVEL=INFO
}

url_debug() {
    show_banner
    echo -e "${YELLOW}🐛 Debug URL-baserad scraper...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att URL-filen finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kopiera filen från HTML-extraktionen.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Första 5 URL:er:${NC}"
    head -5 profile_urls.txt
    echo ""
    
    # Kör debug med URL-baserad spider
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -L DEBUG \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s DOWNLOAD_DELAY=10 \
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
    echo -e "  ${GREEN}run-detached${NC}    Kör full scraping i bakgrunden"
    echo -e "  ${GREEN}stop${NC}            Stoppa alla körande containers"
    echo -e "  ${GREEN}logs${NC}            Visa live loggar från scrapern"
    echo -e "  ${GREEN}shell${NC}           Öppna bash-shell i container"
    echo -e "  ${GREEN}status${NC}          Visa status för containers"
    echo -e "  ${GREEN}clean${NC}           Rensa alla containers och volymer"
    echo -e "  ${GREEN}monitor${NC}        Starta monitoring-interface (port 8080)"
    echo -e "  ${GREEN}verify${NC}         Verifiera Brotli och andra förbättringar"
    echo -e "  ${GREEN}debug${NC}          Kör i debug-läge med detaljerade loggar"
    echo ""
    echo -e "${CYAN}URL-baserade kommandon (kringgår blockerad huvudsida):${NC}"
    echo -e "  ${GREEN}url_test${NC}       Testa URL-baserad scraper (5 profiler)"
    echo -e "  ${GREEN}url_sample${NC}     Scrapa 100 profiler från URL-lista"
    echo -e "  ${GREEN}url_run${NC}        Scrapa alla profiler från URL-lista"
    echo -e "  ${GREEN}url_debug${NC}      Debug URL-baserad scraper"
    echo ""
    echo -e "${CYAN}Chrome Headless-kommandon (använder chromedp/headless-shell):${NC}"
    echo -e "  ${GREEN}chrome_test${NC}     Testa Chrome headless-integration (1 profil)"
    echo -e "  ${GREEN}chrome_sample${NC}   Scrapa 10 profiler med Chrome headless"
    echo -e "  ${GREEN}chrome_run${NC}      Scrapa alla profiler med Chrome headless"
    echo -e "  ${GREEN}chrome_debug${NC}    Debug Chrome headless-scraper"
    echo ""
    echo -e "${YELLOW}Exempel:${NC}"
    echo -e "  $0 build && $0 test     ${PURPLE}# Bygg och testa${NC}"
    echo -e "  $0 url_test             ${PURPLE}# Testa URL-scraper${NC}"
    echo -e "  $0 chrome_test          ${PURPLE}# Testa Chrome headless${NC}"
    echo -e "  $0 chrome_sample        ${PURPLE}# Scrapa 10 profiler med Chrome${NC}"
    echo -e "  $0 logs                 ${PURPLE}# Övervaka framsteg${NC}"
    echo ""
    echo -e "${CYAN}Förbättringar i v2.0:${NC}"
    echo -e "  ✅ Brotli-komprimeringssstöd"
    echo -e "  ✅ 12 realistiska User Agents"
    echo -e "  ✅ Avancerade anti-blocking headers"
    echo -e "  ✅ Adaptiv fördröjning vid 403-fel"
    echo -e "  ✅ Exponential backoff retry-logik"
    echo -e "  ✅ URL-baserad scraping (kringgår blockering)"
    echo -e "  ✅ Chrome headless-integration (ultimat bot-bypass)"
    echo ""
}

# Huvudfunktioner
case "${1:-help}" in
    "build")
        show_banner
        echo -e "${YELLOW}🔨 Bygger Docker-imagen med Enhanced Anti-Blocking...${NC}"
        check_docker
        ensure_directories
        
        # Bygg imagen
        docker-compose build --no-cache
        
        echo -e "${GREEN}✅ Docker-imagen byggd framgångsrikt!${NC}"
        echo -e "${CYAN}💡 Testa nu med: $0 test eller $0 url_test${NC}"
        ;;
        
    "test")
        show_banner
        echo -e "${YELLOW}🧪 Kör test med begränsad scraping...${NC}"
        check_docker
        ensure_directories
        
        # Kör test med begränsning
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
        
        # Kör full scraping
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all
        ;;
        
    "run-detached")
        show_banner
        echo -e "${YELLOW}🚀 Kör full scraping i bakgrunden...${NC}"
        check_docker
        ensure_directories
        
        # Kör i bakgrunden
        docker-compose up -d doppelganger-scraper
        echo -e "${GREEN}✅ Scraper startad i bakgrunden${NC}"
        echo -e "${CYAN}💡 Visa loggar med: $0 logs${NC}"
        echo -e "${CYAN}💡 Stoppa med: $0 stop${NC}"
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
        echo ""
        echo -e "${YELLOW}📈 Docker-statistik:${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
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
        
    "monitor")
        show_banner
        echo -e "${YELLOW}📊 Startar monitoring-interface...${NC}"
        check_docker
        ensure_directories
        
        # Starta monitoring
        docker-compose --profile monitoring up -d scraper-monitor
        echo -e "${GREEN}✅ Monitoring startat på http://localhost:8080${NC}"
        echo -e "${CYAN}💡 Stoppa med: docker-compose --profile monitoring down${NC}"
        ;;
        
    "verify")
        show_banner
        echo -e "${YELLOW}🔍 Verifierar förbättringar...${NC}"
        check_docker
        
        echo -e "${CYAN}Testar Brotli-stöd:${NC}"
        docker-compose run --rm doppelganger-scraper python -c "
import brotli, brotlicffi
print('✅ Brotli support: OK')
print(f'   brotli version: {brotli.__version__}')
print(f'   brotlicffi version: {brotlicffi.__version__}')
"
        
        echo -e "${CYAN}Testar komprimering:${NC}"
        docker-compose run --rm doppelganger-scraper python -c "
import brotli
data = b'Hello Enhanced Doppelganger!'
compressed = brotli.compress(data)
decompressed = brotli.decompress(compressed)
print(f'✅ Compression test: {decompressed.decode()}')
print(f'   Original size: {len(data)} bytes')
print(f'   Compressed size: {len(compressed)} bytes')
print(f'   Compression ratio: {len(compressed)/len(data):.2%}')
"
        
        echo -e "${CYAN}Testar Scrapy-konfiguration:${NC}"
        docker-compose run --rm doppelganger-scraper python -c "
from scrapy.utils.project import get_project_settings
settings = get_project_settings()
print('✅ Scrapy settings loaded')
print(f'   Download delay: {settings.get(\"DOWNLOAD_DELAY\")}s')
print(f'   Concurrent requests: {settings.get(\"CONCURRENT_REQUESTS\")}')
print(f'   Anti-blocking enabled: {settings.get(\"ANTIBLOCK_ENABLED\")}')
print(f'   Retry times: {settings.get(\"RETRY_TIMES\")}')
"
        
        echo -e "${GREEN}✅ Alla verifieringar klara!${NC}"
        ;;
        
    "debug")
        show_banner
        echo -e "${YELLOW}🐛 Kör i debug-läge...${NC}"
        check_docker
        ensure_directories
        
        # Kör med debug och begränsning
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all \
            -L DEBUG \
            -s CLOSESPIDER_ITEMCOUNT=1 \
            -s DOWNLOAD_DELAY=10 \
            -s CONCURRENT_REQUESTS=1
        ;;
        
    "url_test")
        url_test
        ;;
        
    "url_run")
        url_run
        ;;
        
    "url_sample")
        url_sample
        ;;
        
    "url_debug")
        url_debug
        ;;
        
    "chrome_test")
        chrome_test
        ;;
        
    "chrome_sample")
        chrome_sample
        ;;
        
    "chrome_run")
        chrome_run
        ;;
        
    "chrome_debug")
        chrome_debug
        ;;
        
    "help"|*)
        show_help
        ;;
esac

# Chrome Headless-kommandon
chrome_test() {
    show_banner
    echo -e "${YELLOW}🧪 Testar Chrome headless-integration...${NC}"
    check_docker
    
    # Testa Chrome-anslutning från host
    echo -e "${CYAN}🔍 Testar Chrome-anslutning från host...${NC}"
    if command -v python3 &> /dev/null; then
        python3 test_chrome.py
    else
        echo -e "${YELLOW}⚠️  Python3 inte tillgängligt på host, hoppar över anslutningstest${NC}"
    fi
    
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
    
    # Kontrollera att profile_urls.txt finns
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

chrome_run() {
    show_banner
    echo -e "${YELLOW}🚀 Kör Chrome-scraper för alla profiler...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att profile_urls.txt finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kör först url_test för att sätta upp URL-listan.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Antal URL:er att scrapa: $(wc -l < profile_urls.txt)${NC}"
    echo -e "${YELLOW}⚠️  Detta kommer att använda Chrome headless för alla profiler. Fortsätt? (y/N):${NC}"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
            -s LOG_LEVEL=INFO \
            -s CHROME_ENABLED=True \
            -s DOWNLOAD_DELAY=8 \
            -s CONCURRENT_REQUESTS=1
    else
        echo -e "${CYAN}ℹ️  Chrome-scraping avbruten${NC}"
    fi
}

chrome_debug() {
    show_banner
    echo -e "${YELLOW}🐛 Debug Chrome-scraper...${NC}"
    check_docker
    ensure_directories
    
    # Kontrollera att profile_urls.txt finns
    if [ ! -f "profile_urls.txt" ]; then
        echo -e "${RED}❌ profile_urls.txt saknas. Kör först url_test för att sätta upp URL-listan.${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}📊 Första 5 URL:er:${NC}"
    head -5 profile_urls.txt
    echo ""
    
    # Kör debug med Chrome
    docker-compose run --rm doppelganger-scraper scrapy crawl mpb_from_urls \
        -L DEBUG \
        -s CLOSESPIDER_ITEMCOUNT=1 \
        -s CHROME_ENABLED=True \
        -s DOWNLOAD_DELAY=10 \
        -s CONCURRENT_REQUESTS=1
}

