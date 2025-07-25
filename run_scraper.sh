#!/bin/bash

# Doppelganger Scraper Start Script
# Användning: ./run_scraper.sh [alternativ]

set -e

# Färger för output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🕷️  Doppelganger Scraper${NC}"
echo "=================================="

# Kontrollera om Docker är installerat
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker är inte installerat. Installera Docker först.${NC}"
    exit 1
fi

# Kontrollera om docker-compose är installerat
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose är inte installerat. Installera docker-compose först.${NC}"
    exit 1
fi

# Skapa nödvändiga kataloger
mkdir -p images crawls logs

# Sätt rätt behörigheter
chmod 755 images crawls logs

case "${1:-run}" in
    "build")
        echo -e "${YELLOW}🔨 Bygger Docker-image...${NC}"
        docker-compose build
        echo -e "${GREEN}✅ Docker-image byggd!${NC}"
        ;;
    
    "run")
        echo -e "${YELLOW}🚀 Startar scraper...${NC}"
        docker-compose up doppelganger-scraper
        ;;
    
    "run-detached")
        echo -e "${YELLOW}🚀 Startar scraper i bakgrunden...${NC}"
        docker-compose up -d doppelganger-scraper
        echo -e "${GREEN}✅ Scraper körs i bakgrunden. Använd 'docker-compose logs -f' för att se loggar.${NC}"
        ;;
    
    "monitor")
        echo -e "${YELLOW}📊 Startar scraper med monitoring...${NC}"
        docker-compose --profile monitoring up
        ;;
    
    "stop")
        echo -e "${YELLOW}🛑 Stoppar scraper...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Scraper stoppad!${NC}"
        ;;
    
    "logs")
        echo -e "${YELLOW}📋 Visar loggar...${NC}"
        docker-compose logs -f doppelganger-scraper
        ;;
    
    "shell")
        echo -e "${YELLOW}🐚 Öppnar shell i container...${NC}"
        docker-compose run --rm doppelganger-scraper bash
        ;;
    
    "clean")
        echo -e "${YELLOW}🧹 Rensar Docker-resurser...${NC}"
        docker-compose down --rmi all --volumes
        echo -e "${GREEN}✅ Docker-resurser rensade!${NC}"
        ;;
    
    "test")
        echo -e "${YELLOW}🧪 Kör test med begränsad scraping...${NC}"
        docker-compose run --rm doppelganger-scraper scrapy crawl mpb_all -s CLOSESPIDER_ITEMCOUNT=5
        ;;
    
    "help"|*)
        echo "Användning: $0 [kommando]"
        echo ""
        echo "Kommandon:"
        echo "  build         Bygg Docker-image"
        echo "  run           Kör scraper (standard)"
        echo "  run-detached  Kör scraper i bakgrunden"
        echo "  monitor       Kör scraper med web-monitoring"
        echo "  stop          Stoppa scraper"
        echo "  logs          Visa loggar"
        echo "  shell         Öppna shell i container"
        echo "  test          Kör test med begränsad scraping"
        echo "  clean         Rensa Docker-resurser"
        echo "  help          Visa denna hjälp"
        echo ""
        echo "Exempel:"
        echo "  $0 build      # Bygg imagen först"
        echo "  $0 test       # Testa med några få items"
        echo "  $0 run        # Kör full scraping"
        ;;
esac

