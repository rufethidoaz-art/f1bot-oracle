"""
F1 Telegram Bot - Live Timing Version
Enhanced version with live timing functionality
"""

import os
import sys
import asyncio
import requests
import json
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Playwright imports for F1 timing scraping
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Live timing will use API fallback only.")

# Configure logging optimized for Leapcell limits (WARNING level to reduce log storage)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Azerbaijani translations (simplified)
TRANSLATIONS = {
    "welcome_title": "🏎️ F1 Canlı Botuna Xoş Gəlmisiniz!",
    "welcome_text": """🏁 Sizin Formula 1 üçün ən yaxşı yoldaşınız - real vaxt yarış məlumatları, sıralamalar və canlı vaxt məlumatları.

*Edə biləcəyiniz:*
🏆 Cari çempionat sıralamalarını yoxlayın
🏎️ Son nəticələri alın
📅 Gələn yarış cədvəllərini və hava proqnozunu (Bakı vaxtı ilə) görün
🔴 Canlı vaxtı izləyin""",
    "menu_title": "🏎️ F1 Bot Menyusu",
    "menu_text": "Aşağıdakı variantlardan birini seçin:",
    "driver_standings": "🏆 Sürücü Sıralamaları",
    "constructor_standings": "🏁 Konstruktor Sıralamaları",
    "last_session": "🏎️ Son Sessiya Nəticələri",
    "schedule_weather": "📅 Cədvəl & Hava",
    "live_timing": "🔴 Canlı Vaxt",
    "help_commands_btn": "ℹ️ Kömək & Əmrlər",
    "season_driver_standings": " Pilotların Çempionat Sıralaması",
    "season_constructor_standings": "*Konstruktorların Çempionat Sıralaması- {}*",
    "points": "xal",
    "qualifying": "Təsnifat",
    "sprint": "Sprint",
    "race": "Yarış",
    "winner": " - Qalib",
    "fastest_lap": "Ən Sürətli Dövrə: {} ({})",
    "next_race": "🏎️ *Gələn Yarış*",
    "fp1": "FP1",
    "fp2": "FP2",
    "fp3": "FP3",
    "sprint_qualifying": "Sprint Təsnifatı",
    "qualifying": "Təsnifat",
    "race": "Yarış",
    "all_times_baku": "_Bütün vaxtlar Bakı vaxtı ilə_",
    "season_completed": "🏁 Mövsüm tamamlandı! Bu il üçün daha yarış yoxdur.",
    "weather_forecast": "🌤️ Hava Proqnozu üçün {}",
    "friday": "Cümə",
    "saturday": "Şənbə",
    "sunday": "Bazar",
    "race_day": "Bazar (Yarış)",
    "weather_unavailable": "🌦️ Bu yer üçün hava məlumatları mövcud deyil.",
    "no_live_data": "❌ Canlı vaxt məlumatları mövcud deyil\n\nSon nəticələr üçün /lastrace istifadə edin",
    "live_not_available": "❌ Canlı vaxt mövcud deyil\n\nSon nəticələr üçün /lastrace istifadə edin",
    "loading": "⏳ Yüklənir...",
    "api_unavailable": "❌ Xidmət mənbəyi baxımdadır. Bir neçə dəqiqə sonra yenidən cəhd edin.",
    "no_standings": "❌ Bu mövsüm üçün sıralama məlumatları tapılmadı.",
    "no_driver_standings": "❌ Sürücü sıralamaları tapılmadı.",
    "invalid_data": "❌ Mənbədən yanlış məlumat format.",
    "no_constructor_standings": "❌ Konstruktor sıralamaları tapılmadı.",
    "no_sessions": "❌ Sessiya tapılmadı. API offline ola bilər.",
    "no_recent_sessions": "❌ Son tamamlanmış sessiyalar tapılmadı.",
    "no_results": "❌ Bu sessiya üçün nəticələr mövcud deyil.",
    "no_position_data": "❌ Bu sessiya üçün mövqe məlumatları mövcud deyil.",
    "no_final_positions": "❌ Bu sessiya üçün final mövqelər mövcud deyil.",
    "error_fetching_session": "❌ Sessiya nəticələrini almaqda xəta: {}",
    "error_fetching_race": "❌ Gələn yarış alınarkən xəta: {}",
    "weather_unavailable": "❌ Hava məlumatları mövcud deyil.",
    "error_fetching_weather": "❌ Hava məlumatları alınarkən xəta: {}",
    "service_unavailable": "❌ Xidmət müvəqqəti mövcud deyil. Daha sonra yenidən cəhd edin.",
    "error_occurred": "❌ Xəta baş verdi: {}",
    "unknown_command": "❌ Naməlum əmr",
    "live_session_check": "🔴 Canlı sessiya yoxlanılır...",
    "live_session_active": "🔴 Canlı sessiya aktivdir! Mövqelər yenilənir...",
    "live_session_inactive": "🔴 Hal-hazırda aktiv F1 sessiyası yoxdur",
    "live_session_error": "❌ Canlı sessiya yoxlanarkən xəta: {}",
    "live_timing_available": "🔴 Canlı vaxt mövcuddur!",
    "live_timing_unavailable": "❌ Canlı vaxt mövcud deyil",
    "live_positions_loading": "⏳ Mövqe məlumatları yüklənir...",
    "live_data_source": "ℹ️ *Mənbə:* OpenF1 API",
    "live_refresh_button": "🔄 Yenilə",
    "live_positions_header": "📊 *Cari Mövqelər:*",
    "live_session_location": "📍 *Məkan:*",
    "live_session_time": "🕐 *Başlama vaxtı:*",
    "live_update_frequency": "🔄 *Məlumatlar hər 15 saniyədə yenilənir*",
    "live_position_winner": "🏆",
    "live_session_info_error": "Sessiya məlumatları natamam",
    "live_positions_error": "Mövqe məlumatları mövcud deyil",
}

# Country to flag emoji mapping
COUNTRY_FLAGS = {
    "Mexico": "🇲🇽",
    "Mexico City": "🇲🇽",
    "USA": "🇺🇸",
    "United States": "🇺🇸",
    "Austin": "🇺🇸",
    "Miami": "🇺🇸",
    "Las Vegas": "🇺🇸",
    "Brazil": "🇧🇷",
    "UK": "🇬🇧",
    "United Kingdom": "🇬🇧",
    "Monaco": "🇲🇨",
    "Italy": "🇮🇹",
    "Imola": "🇮🇹",
    "Monza": "🇮🇹",
    "Spain": "🇪🇸",
    "Australia": "🇦🇺",
    "Netherlands": "🇳🇱",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Austria": "🇦🇹",
    "Canada": "🇨🇦",
    "Japan": "🇯🇵",
    "Singapore": "🇸🇬",
    "Bahrain": "🇧🇭",
    "Saudi Arabia": "🇸🇦",
    "Qatar": "🇶🇦",
    "UAE": "🇦🇪",
    "United Arab Emirates": "🇦🇪",
    "Abu Dhabi": "🇦🇪",
    "China": "🇨🇳",
    "Belgium": "🇧🇪",
    "Hungary": "🇭🇺",
    "Portugal": "🇵🇹",
    "Russia": "🇷🇺",
    "Turkey": "🇹🇷",
    "Azerbaijan": "🇦🇿",
    "Baku": "🇦🇿",
    "British": "🇬🇧",
    "Australian": "🇦🇺",
    "Dutch": "🇳🇱",
    "Monegasque": "🇲🇨",
    "Spanish": "🇪🇸",
    "Mexican": "🇲🇽",
    "German": "🇩🇪",
    "French": "🇫🇷",
    "Japanese": "🇯🇵",
    "Canadian": "🇨🇦",
    "Thai": "🇹🇭",
    "Finnish": "🇫🇮",
    "Chinese": "🇨🇳",
    "Danish": "🇩🇰",
    "American": "🇺🇸",
    "Austrian": "🇦🇹",
    "Italian": "🇮🇹",
    "Brazilian": "🇧🇷",
    "New Zealander": "🇳🇿",
    "Polish": "🇵🇱",
    "Swiss": "🇨🇭",
    "South African": "🇿🇦",
    "Venezuelan": "🇻🇪",
    "Indonesian": "🇮🇩",
    "Argentine": "🇦🇷",
    # Country codes (for OpenF1 API) - IOC codes
    "NED": "🇳🇱",
    "GBR": "🇬🇧",
    "AUS": "🇦🇺",
    "MCO": "🇲🇨",
    "ESP": "🇪🇸",
    "MEX": "🇲🇽",
    "GER": "🇩🇪",
    "FRA": "🇫🇷",
    "JPN": "🇯🇵",
    "CAN": "🇨🇦",
    "THA": "🇹🇭",
    "FIN": "🇫🇮",
    "CHN": "🇨🇳",
    "DEN": "🇩🇰",
    "USA": "🇺🇸",
    "AUT": "🇦🇹",
    "ITA": "🇮🇹",
    "BRA": "🇧🇷",
    "NZL": "🇳🇿",
    "RUS": "🇷🇺",
    "POL": "🇵🇱",
    "CHE": "🇨🇭",
    "ZAF": "🇿🇦",
    "VEN": "🇻🇪",
    "IDN": "🇮🇩",
    "ARG": "🇦🇷",
}

# Global driver and constructor data cache
DRIVER_DATA_CACHE = {}
CONSTRUCTOR_DATA_CACHE = {}

def get_driver_data(season=None):
    """Fetch driver data from Ergast API with caching"""
    global DRIVER_DATA_CACHE

    if season is None:
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1

    cache_key = f"drivers_{season}"
    if cache_key in DRIVER_DATA_CACHE:
        cached = DRIVER_DATA_CACHE[cache_key]
        if cached.get('timestamp') and (datetime.now(ZoneInfo("UTC")).timestamp() - cached['timestamp']) < 86400:  # 24 hours
            return cached['data']

    try:
        logger.info(f"Fetching driver data for season {season}")
        url = f"https://api.jolpi.ca/ergast/f1/{season}/drivers.json"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            drivers = {}

            driver_list = data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
            for driver in driver_list:
                driver_id = driver.get("driverId")
                if driver_id:
                    drivers[driver_id] = {
                        'driverId': driver_id,
                        'permanentNumber': driver.get('permanentNumber'),
                        'code': driver.get('code'),
                        'givenName': driver.get('givenName', ''),
                        'familyName': driver.get('familyName', ''),
                        'full_name': f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                        'nationality': driver.get('nationality', ''),
                        'dateOfBirth': driver.get('dateOfBirth'),
                        'url': driver.get('url')
                    }

            # Cache the data
            DRIVER_DATA_CACHE[cache_key] = {
                'data': drivers,
                'timestamp': datetime.now(ZoneInfo("UTC")).timestamp()
            }

            return drivers
        else:
            logger.error(f"Failed to fetch driver data: {response.status_code}")
            return {}

    except Exception as e:
        logger.error(f"Error fetching driver data: {e}")
        return {}

def get_constructor_data(season=None):
    """Fetch constructor data from Ergast API with caching"""
    global CONSTRUCTOR_DATA_CACHE

    if season is None:
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1

    cache_key = f"constructors_{season}"
    if cache_key in CONSTRUCTOR_DATA_CACHE:
        cached = CONSTRUCTOR_DATA_CACHE[cache_key]
        if cached.get('timestamp') and (datetime.now(ZoneInfo("UTC")).timestamp() - cached['timestamp']) < 86400:  # 24 hours
            return cached['data']

    try:
        logger.info(f"Fetching constructor data for season {season}")
        url = f"https://api.jolpi.ca/ergast/f1/{season}/constructors.json"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            data = response.json()
            constructors = {}

            constructor_list = data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", [])
            for constructor in constructor_list:
                constructor_id = constructor.get("constructorId")
                if constructor_id:
                    constructors[constructor_id] = {
                        'constructorId': constructor_id,
                        'name': constructor.get('name', ''),
                        'nationality': constructor.get('nationality', ''),
                        'url': constructor.get('url')
                    }

            # Cache the data
            CONSTRUCTOR_DATA_CACHE[cache_key] = {
                'data': constructors,
                'timestamp': datetime.now(ZoneInfo("UTC")).timestamp()
            }

            return constructors
        else:
            logger.error(f"Failed to fetch constructor data: {response.status_code}")
            return {}

    except Exception as e:
        logger.error(f"Error fetching constructor data: {e}")
        return {}

def get_driver_nationality_by_number(driver_number, season=None):
    """Get driver nationality by permanent number"""
    drivers = get_driver_data(season)
    for driver_id, driver_info in drivers.items():
        if str(driver_info.get('permanentNumber', '')) == str(driver_number):
            return driver_info.get('nationality', '')
    return ''

def get_driver_name_by_number(driver_number, season=None):
    """Get driver name by permanent number"""
    drivers = get_driver_data(season)
    for driver_id, driver_info in drivers.items():
        if str(driver_info.get('permanentNumber', '')) == str(driver_number):
            return driver_info.get('full_name', f'Driver {driver_number}')
    return f'Driver {driver_number}'

def get_constructor_name_by_id(constructor_id, season=None):
    """Get constructor name by ID"""
    constructors = get_constructor_data(season)
    constructor = constructors.get(constructor_id, {})
    return constructor.get('name', constructor_id)

# Comprehensive F1 circuit coordinates for weather API
CIRCUIT_COORDS = {
    # Current F1 Circuits (2024-2025) - Official names
    "Bahrain International Circuit": (26.0325, 50.5106),
    "Jeddah Corniche Circuit": (21.6319, 39.1044),
    "Albert Park Circuit": (-37.8497, 144.9680),
    "Suzuka Circuit": (34.8431, 136.5410),
    "Shanghai International Circuit": (31.3389, 121.2197),
    "Miami International Autodrome": (25.9581, -80.2389),
    "Autodromo Enzo e Dino Ferrari": (44.3439, 11.7167),
    "Circuit de Monaco": (43.7347, 7.4206),
    "Circuit de Barcelona-Catalunya": (41.5699, 2.2570),
    "Circuit Gilles Villeneuve": (45.5000, -73.5228),
    "Red Bull Ring": (47.2197, 14.7647),
    "Silverstone Circuit": (52.0720, -1.0170),
    "Hungaroring": (47.5789, 19.2486),
    "Circuit de Spa-Francorchamps": (50.4372, 5.9714),
    "Circuit Zandvoort": (52.3888, 4.5409),
    "Autodromo Nazionale di Monza": (45.6190, 9.2816),
    "Marina Bay Street Circuit": (1.2914, 103.8632),
    "Baku City Circuit": (40.4093, 49.8671),
    "Circuit of the Americas": (30.1328, -97.6411),
    "Autodromo Hermanos Rodriguez": (19.4042, -99.0907),
    "Autodromo Jose Carlos Pace": (-23.7036, -46.6997),
    "Las Vegas Street Circuit": (36.1147, -115.1739),
    "Lusail International Circuit": (25.4888, 51.4543),
    "Yas Marina Circuit": (24.4672, 54.6031),
    # Alternative/common names for matching
    "Sakhir": (26.0325, 50.5106),
    "Jeddah": (21.6319, 39.1044),
    "Melbourne": (-37.8497, 144.9680),
    "Suzuka": (34.8431, 136.5410),
    "Shanghai": (31.3389, 121.2197),
    "Miami": (25.9581, -80.2389),
    "Imola": (44.3439, 11.7167),
    "Monaco": (43.7347, 7.4206),
    "Barcelona": (41.5699, 2.2570),
    "Montreal": (45.5000, -73.5228),
    "Spielberg": (47.2197, 14.7647),
    "Silverstone": (52.0720, -1.0170),
    "Budapest": (47.5789, 19.2486),
    "Spa": (50.4372, 5.9714),
    "Zandvoort": (52.3888, 4.5409),
    "Monza": (45.6190, 9.2816),
    "Singapore": (1.2914, 103.8632),
    "Baku": (40.4093, 49.8671),
    "Austin": (30.1328, -97.6411),
    "Mexico City": (19.4042, -99.0907),
    "Sao Paulo": (-23.7036, -46.6997),
    "Interlagos": (-23.7036, -46.6997),
    "Las Vegas": (36.1147, -115.1739),
    "Lusail": (25.4888, 51.4543),
    "Abu Dhabi": (24.4672, 54.6031),
}


def get_country_flag(nationality):
    """Get flag emoji for a nationality"""
    if not nationality:
        return "🏳️"

    nationality = nationality.strip()

    # Direct lookup (handles exact matches including 3-letter codes)
    if nationality in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality]

    # Try uppercase (for country codes like NED, GBR)
    if nationality.upper() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.upper()]

    # Try lowercase
    if nationality.lower() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.lower()]

    # Try title case
    if nationality.title() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.title()]

    # Partial match
    nationality_lower = nationality.lower()
    for key, flag in COUNTRY_FLAGS.items():
        if key.lower() in nationality_lower or nationality_lower in key.lower():
            return flag

    return "🏳️"


def to_baku(d, t):
    """Convert UTC time to Baku time"""
    if not t or t == "TBA":
        return f"{d} (TBA)"
    try:
        # strip trailing Z if present
        tzinfo = ZoneInfo("UTC")
        if t.endswith("Z"):
            t2 = t[:-1]
        else:
            t2 = t
        dt = datetime.fromisoformat(d + "T" + t2)
        # assume dt is UTC if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzinfo)
        baku = dt.astimezone(ZoneInfo("Asia/Baku"))
        date_str = baku.strftime("%d %b")
        time_str = baku.strftime("%H:%M")
        return f"{date_str} {time_str}"
    except Exception:
        return f"{d} {t}"


def get_circuit_coordinates(location_name):
    """Get coordinates for a circuit with fuzzy matching"""
    # Direct match first
    if location_name in CIRCUIT_COORDS:
        return CIRCUIT_COORDS[location_name]

    # Fuzzy matching for partial names
    location_lower = location_name.lower()
    for circuit_name, coords in CIRCUIT_COORDS.items():
        if (
            location_lower in circuit_name.lower()
            or circuit_name.lower() in location_lower
        ):
            return coords

    # Geocoding fallback
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1"
        response = requests.get(geo_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                return (result["latitude"], result["longitude"])
    except Exception:
        pass

    return None


def check_active_f1_session():
    """Check if there's currently an active F1 session using OpenF1 API with caching"""
    try:
        # Check cache first
        cached = get_cached_data("active_session")
        if cached is not None:
            return cached

        logger.info(TRANSLATIONS["live_session_check"])
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year

        # Check current and next year for sessions
        years_to_check = [current_year]
        if now.month >= 11:
            years_to_check.append(current_year + 1)

        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=10)
                if sessions_response.status_code == 200:
                    sessions.extend(sessions_response.json())
            except Exception as e:
                logger.error(f"Error fetching sessions for year {year}: {e}")
                continue

        if not sessions:
            logger.warning("No sessions found")
            set_cached_data("active_session", False)
            return False

        # Check if any session is currently active (within the last 2 hours and next 4 hours)
        for session in sessions:
            session_start = session.get("date_start")
            session_end = session.get("date_end")

            if session_start:
                try:
                    start_dt = datetime.fromisoformat(
                        session_start.replace("Z", "+00:00")
                    )
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))

                    # Check if session is currently running or will start soon
                    time_diff_start = (start_dt - now).total_seconds() / 3600  # hours
                    time_diff_end = 0

                    if session_end:
                        end_dt = datetime.fromisoformat(
                            session_end.replace("Z", "+00:00")
                        )
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=ZoneInfo("UTC"))
                        time_diff_end = (end_dt - now).total_seconds() / 3600  # hours

                        # Session is active if it started within last 2 hours and hasn't ended + 1 hour grace period
                        if (
                            -2 <= time_diff_start <= 0 and time_diff_end > -1
                        ):  # Allow 1 hour after session ends
                            logger.info(
                                f"Active session found: {session.get('session_name', 'Unknown')}"
                            )
                            set_cached_data("active_session", True)
                            return True
                    else:
                        # If no end time, check if session started recently (within 2 hours)
                        if (
                            -2 <= time_diff_start <= 1
                        ):  # Allow 1 hour future for upcoming sessions
                            logger.info(
                                f"Upcoming session found: {session.get('session_name', 'Unknown')}"
                            )
                            set_cached_data("active_session", True)
                            return True

                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing session times: {e}")
                    continue

        logger.info(TRANSLATIONS["live_session_inactive"])
        set_cached_data("active_session", False)
        return False

    except Exception as e:
        logger.error(f"{TRANSLATIONS['live_session_error'].format(str(e))}")
        set_cached_data("active_session", False)
        return False


def get_current_standings():
    """Get current F1 driver standings with caching"""
    try:
        # Check cache first
        cached = get_cached_data("standings")
        if cached:
            return cached

        logger.info("Fetching current standings from API")
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1

        # Try multiple APIs with better error handling
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}/driverStandings.json",
        ]

        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except Exception as e:
                logger.error(f"Error fetching standings from {api_url}: {e}")
                continue

        if not data:
            return TRANSLATIONS["api_unavailable"]

        try:
            standings_list = (
                data.get("MRData", {})
                .get("StandingsTable", {})
                .get("StandingsLists", [])
            )
            if not standings_list:
                return TRANSLATIONS["no_standings"]

            standings = standings_list[0].get("DriverStandings", [])
            if not standings:
                return TRANSLATIONS["no_driver_standings"]

            actual_season = standings_list[0].get("season", season)
        except Exception as e:
            logger.error(f"Error parsing standings data: {e}")
            return TRANSLATIONS["invalid_data"]

        message = f"🏆 {actual_season} {TRANSLATIONS['season_driver_standings']}\n\n"

        for driver in standings:
            try:
                pos = driver.get("position", "?")
                driver_info = driver.get("Driver", {})
                given_name = driver_info.get("givenName", "Unknown")
                family_name = driver_info.get("familyName", "Driver")
                full_name = f"{given_name} {family_name.upper()}"
                nationality = driver_info.get("nationality", "")
                flag = get_country_flag(nationality)
                points = driver.get("points", "0")

                message += (
                    f"{pos}. {flag} {full_name} ({points} {TRANSLATIONS['points']})\n"
                )
            except Exception as e:
                logger.error(f"Error processing driver data: {e}")
                continue

        # Cache the result
        set_cached_data("standings", message)
        return message
    except Exception as e:
        logger.error(f"Error in get_current_standings: {e}")
        return TRANSLATIONS["service_unavailable"]


def get_constructor_standings():
    """Get constructor standings with caching"""
    try:
        # Check cache first
        cached = get_cached_data("constructor_standings")
        if cached:
            return cached

        logger.info("Fetching constructor standings from API")
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1

        # Try multiple APIs
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}/constructorStandings.json",
        ]

        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except Exception as e:
                logger.error(
                    f"Error fetching constructor standings from {api_url}: {e}"
                )
                continue

        if not data:
            return TRANSLATIONS["api_unavailable"]

        try:
            standings_list = (
                data.get("MRData", {})
                .get("StandingsTable", {})
                .get("StandingsLists", [])
            )
            if not standings_list:
                return TRANSLATIONS["no_constructor_standings"]

            standings = standings_list[0].get("ConstructorStandings", [])
            if not standings:
                return TRANSLATIONS["no_constructor_standings"]

            actual_season = standings_list[0].get("season", season)
        except Exception as e:
            logger.error(f"Error parsing constructor standings data: {e}")
            return TRANSLATIONS["invalid_data"]

        # Get constructor data for dynamic flag mapping
        constructors_data = get_constructor_data(actual_season)
        team_flags = {}
        for constructor_id, constructor_info in constructors_data.items():
            team_name = constructor_info.get('name', '')
            nationality = constructor_info.get('nationality', '')
            flag = get_country_flag(nationality)
            if flag != "🏳️":  # Only add if we have a valid flag
                team_flags[team_name] = flag

        # Fallback hardcoded flags for common teams
        fallback_flags = {
            "Red Bull": "🇦🇹",
            "Ferrari": "🇮🇹",
            "Mercedes": "🇩🇪",
            "McLaren": "🇬🇧",
            "Aston Martin": "🇬🇧",
            "Alpine": "🇫🇷",
            "Williams": "🇬🇧",
            "AlphaTauri": "🇮🇹",
            "RB": "🇮🇹",
            "Alfa Romeo": "🇨🇭",
            "Sauber": "🇨🇭",
            "Haas": "🇺🇸",
        }
        team_flags.update(fallback_flags)

        message = f"🏆 *{TRANSLATIONS['season_constructor_standings'].format(actual_season)}*\n\n"

        for pos, team in enumerate(standings, 1):
            try:
                constructor = team.get("Constructor", {})
                team_name = constructor.get("name", "Unknown Team")
                points = team.get("points", "0")

                flag = ""
                for key, emoji in team_flags.items():
                    if key in team_name:
                        flag = emoji + " "
                        break

                message += (
                    f"{pos}. {flag}*{team_name}* - {points} {TRANSLATIONS['points']}\n"
                )
            except Exception as e:
                logger.error(f"Error processing team data: {e}")
                continue

        # Cache the result
        set_cached_data("constructor_standings", message)
        return message
    except Exception as e:
        logger.error(f"Error in get_constructor_standings: {e}")
        return TRANSLATIONS["service_unavailable"]


def get_last_session_results():
    """Get last session results using OpenF1 API with enhanced data and caching"""
    try:
        # Check cache first
        cached = get_cached_data("last_session")
        if cached:
            return cached

        logger.info("Fetching last session results from API")
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year

        years_to_check = [current_year]
        if now.month <= 3:
            years_to_check.insert(0, current_year - 1)

        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=10)
                if sessions_response.status_code == 200:
                    sessions.extend(sessions_response.json())
            except Exception as e:
                logger.error(f"Error fetching sessions for year {year}: {e}")
                continue

        if not sessions:
            return TRANSLATIONS["no_sessions"]

        latest_session = None
        for session in reversed(sessions):
            session_start = session.get("date_start")
            session_type = session.get("session_type")

            if session_start and session_type in ["Qualifying", "Sprint", "Race"]:
                try:
                    start_dt = datetime.fromisoformat(
                        session_start.replace("Z", "+00:00")
                    )
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))

                    if start_dt < (now - timedelta(hours=2)):
                        latest_session = session
                        break
                except Exception as e:
                    logger.error(f"Error parsing session start time: {e}")
                    continue

        if not latest_session:
            return TRANSLATIONS["no_recent_sessions"]

        session_key = latest_session.get("session_key")
        session_type = latest_session.get("session_type")
        meeting_name = latest_session.get("meeting_name", "Grand Prix")
        country_name = latest_session.get("country_name", "")
        flag = get_country_flag(country_name)

        # Get positions
        results_url = f"https://api.openf1.org/v1/position?session_key={session_key}"
        results_response = requests.get(results_url, timeout=10)
        if results_response.status_code != 200:
            return TRANSLATIONS["no_results"].format(session_type)

        positions_data = results_response.json()
        if not positions_data:
            return TRANSLATIONS["no_position_data"].format(session_type)

        final_positions = {}
        for pos_entry in positions_data:
            driver_number = pos_entry.get("driver_number")
            position = pos_entry.get("position")
            date = pos_entry.get("date")

            if driver_number and position and date:
                if (
                    driver_number not in final_positions
                    or date > final_positions[driver_number]["date"]
                ):
                    final_positions[driver_number] = {
                        "position": position,
                        "date": date,
                    }

        # Get driver info from OpenF1 API first, then fallback to Ergast
        drivers_url = f"https://api.openf1.org/v1/drivers?session_key={session_key}"
        drivers_response = requests.get(drivers_url, timeout=10)
        drivers_info = {}
        if drivers_response.status_code == 200:
            for driver in drivers_response.json():
                driver_number = driver.get("driver_number")
                if driver_number:
                    driver_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
                    country_code = driver.get("country_code") or get_driver_nationality_by_number(driver_number)

                    drivers_info[driver_number] = {
                        "name": driver_name or get_driver_name_by_number(driver_number),
                        "country": country_code,
                        "team": driver.get("team_name", ""),
                    }

        sorted_positions = sorted(
            final_positions.items(), key=lambda x: x[1]["position"]
        )
        if not sorted_positions:
            return TRANSLATIONS["no_final_positions"].format(session_type)

        emoji = (
            "🏁"
            if session_type == "Sprint"
            else "⏱️" if session_type == "Qualifying" else "🏆"
        )
        session_type_az = TRANSLATIONS.get(session_type.lower(), session_type)
        message = f"{emoji} {flag} *{meeting_name} {session_type_az}*\n\n"

        for driver_number, pos_data in sorted_positions[:20]:
            position = pos_data["position"]
            driver_info = drivers_info.get(driver_number, {})
            driver_name = driver_info.get("name", f"Driver {driver_number}")
            driver_country = driver_info.get("country", "")
            driver_flag = get_country_flag(driver_country)
            team_name = driver_info.get("team", "")

            line = f"{position}. {driver_flag} {driver_name}"

            if session_type in ["Race", "Sprint"] and team_name:
                line += f" ({team_name})"

            if position == 1:
                line += f" - {TRANSLATIONS['winner']}"

            message += line + "\n"

        # Cache the result
        set_cached_data("last_session", message)
        return message

    except Exception as e:
        logger.error(f"Error in get_last_session_results: {e}")
        return TRANSLATIONS["error_fetching_session"].format(str(e))


def get_f1_season_calendar():
    """Fetch and display the current F1 season's race schedule"""
    try:
        logger.info("Fetching F1 season calendar")
        now = datetime.now(ZoneInfo("UTC"))
        season = now.year if now.month >= 1 else now.year - 1

        # Try multiple APIs
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}.json",
        ]

        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except Exception as e:
                logger.error(f"Error fetching calendar from {api_url}: {e}")
                continue

        if not data:
            return TRANSLATIONS["api_unavailable"]

        try:
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                return TRANSLATIONS["no_race_schedule"]
        except Exception as e:
            logger.error(f"Error parsing calendar data: {e}")
            return TRANSLATIONS["invalid_data"]

        # Check for sprint weekends using OpenF1 API
        sprint_weekends = {}
        try:
            sessions_url = f"https://api.openf1.org/v1/sessions?year={season}"
            sessions_response = requests.get(sessions_url, timeout=10)
            if sessions_response.status_code == 200:
                sessions = sessions_response.json()
                for session in sessions:
                    if session.get("session_name") == "Sprint":
                        country_name = session.get("country_name", "")
                        if country_name:
                            sprint_weekends[country_name] = True
        except Exception as e:
            logger.warning(f"Could not fetch sprint data from OpenF1: {e}")

        message = f"{season} F1 Mövsüm Cədvəli\n\n"

        for race in races:
            try:
                race_name = race.get("raceName", "Grand Prix")
                circuit = race.get("Circuit", {})
                location = circuit.get("Location", {})
                locality = location.get("locality", "")
                country = location.get("country", "")
                race_date = race.get("date")
                race_time = race.get("time", "TBA")

                flag = get_country_flag(country)

                # Calculate weekend range based on race date (typically Sunday)
                # F1 weekends run Friday to Sunday
                try:
                    # Handle different date formats from API
                    if 'T' in race_date:
                        race_dt = datetime.fromisoformat(race_date)
                    else:
                        # Handle date-only format like "2026-03-08"
                        race_dt = datetime.strptime(race_date, "%Y-%m-%d")
                    
                    # Race is usually on Sunday, so weekend starts Friday
                    weekend_start = race_dt - timedelta(days=2)  # Friday
                    weekend_end = race_dt  # Sunday (race day)

                    # Format as "Mar 03-05"
                    if weekend_start.month == weekend_end.month:
                        weekend_range = f"{weekend_start.strftime('%b')} {weekend_start.day}-{weekend_end.day}"
                    else:
                        weekend_range = f"{weekend_start.strftime('%b %d')}-{weekend_end.strftime('%b %d')}"
                except Exception as e:
                    # Fallback to just race date if parsing fails
                    logger.warning(f"Could not calculate weekend range for {race_date}: {e}")
                    baku_race_time = to_baku(race_date, race_time)
                    weekend_range = baku_race_time.split()[0] if ' ' in baku_race_time else baku_race_time

                # Check if this is a sprint weekend
                is_sprint_weekend = sprint_weekends.get(country, False)
                sprint_indicator = " Sprint" if is_sprint_weekend else ""

                message += f"{flag} {locality}, {weekend_range}{sprint_indicator}\n"

            except Exception as e:
                logger.error(f"Error processing race data: {e}")
                continue

        return message
    except Exception as e:
        logger.error(f"Error in get_f1_season_calendar: {e}")
        return TRANSLATIONS["error_fetching_race"].format(str(e))


def get_next_race():
    """Get next race schedule using Jolpica API with caching"""
    try:
        # Check cache first
        cached = get_cached_data("next_race")
        if cached:
            return cached

        logger.info("Fetching next race schedule from API")
        now = datetime.now(ZoneInfo("UTC"))
        season = now.year if now.month >= 1 else now.year - 1

        # Try multiple APIs
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}.json",
        ]

        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except Exception as e:
                logger.error(f"Error fetching race schedule from {api_url}: {e}")
                continue

        if not data:
            return TRANSLATIONS["api_unavailable"]

        try:
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                return TRANSLATIONS["no_race_schedule"]
        except Exception as e:
            logger.error(f"Error parsing race data: {e}")
            return TRANSLATIONS["invalid_data"]

        # Find next race
        next_race = None
        for race in races:
            try:
                race_date = race.get("date")
                race_time = race.get("time", "00:00")

                if race_date:
                    race_dt_str = f"{race_date}T{race_time.replace('Z', '')}"
                    race_dt = datetime.fromisoformat(race_dt_str)
                    if race_dt.tzinfo is None:
                        race_dt = race_dt.replace(tzinfo=ZoneInfo("UTC"))

                    if race_dt >= now:
                        next_race = race
                        break
            except Exception as e:
                logger.error(f"Error parsing race date/time: {e}")
                continue

        if not next_race:
            return TRANSLATIONS["season_completed"]

        # Extract race info
        race_name = next_race.get("raceName", "Grand Prix")
        circuit = next_race.get("Circuit", {})
        location = circuit.get("Location", {})
        locality = location.get("locality", "")
        country = location.get("country", "")

        flag = get_country_flag(country)

        message = f"{TRANSLATIONS['next_race']}\n"
        message += f"{flag} *{race_name}*\n\n"

        # Collect all sessions with times
        sessions = []

        # FP1
        fp1 = next_race.get("FirstPractice", {})
        fp1_date = fp1.get("date")
        fp1_time = fp1.get("time", "TBA")
        if fp1_date and fp1_time != "TBA":
            sessions.append((fp1_date, fp1_time, TRANSLATIONS["fp1"]))

        # FP2
        fp2 = next_race.get("SecondPractice", {})
        fp2_date = fp2.get("date")
        fp2_time = fp2.get("time", "TBA")
        if fp2_date and fp2_time != "TBA":
            sessions.append((fp2_date, fp2_time, TRANSLATIONS["fp2"]))

        # FP3
        fp3 = next_race.get("ThirdPractice", {})
        fp3_date = fp3.get("date")
        fp3_time = fp3.get("time", "TBA")
        if fp3_date and fp3_time != "TBA":
            sessions.append((fp3_date, fp3_time, TRANSLATIONS["fp3"]))

        # Sprint Qualifying
        sprint_quali = next_race.get("SprintQualifying", {})
        sq_date = sprint_quali.get("date")
        sq_time = sprint_quali.get("time", "TBA")
        if sq_date and sq_time != "TBA":
            sessions.append((sq_date, sq_time, TRANSLATIONS["sprint_qualifying"]))

        # Sprint
        sprint = next_race.get("Sprint", {})
        sprint_date = sprint.get("date")
        sprint_time = sprint.get("time", "TBA")
        if sprint_date and sprint_time != "TBA":
            sessions.append((sprint_date, sprint_time, TRANSLATIONS["sprint"]))

        # Qualifying
        quali = next_race.get("Qualifying", {})
        quali_date = quali.get("date")
        quali_time = quali.get("time", "TBA")
        if quali_date and quali_time != "TBA":
            sessions.append((quali_date, quali_time, TRANSLATIONS["qualifying"]))

        # Race
        race_date = next_race.get("date")
        race_time = next_race.get("time", "TBA")
        if race_date and race_time != "TBA":
            sessions.append((race_date, race_time, TRANSLATIONS["race"]))

        # Sort sessions by date and time
        sessions.sort(key=lambda x: (x[0], x[1]))

        # Display sessions in chronological order
        for session_date, session_time, session_name in sessions:
            baku_time = to_baku(session_date, session_time)
            message += f"*{session_name}:* {baku_time}\n"

        message += f"\n_{TRANSLATIONS['all_times_baku']}_\n"

        # Add weather forecast with separate caching
        weather_cached = get_cached_data("weather")
        if weather_cached:
            message += weather_cached
        else:
            try:
                coords = get_circuit_coordinates(locality)
                if coords and race_date:
                    race_date_obj = datetime.fromisoformat(race_date)
                    friday = race_date_obj - timedelta(days=2)
                    saturday = race_date_obj - timedelta(days=1)
                    sunday = race_date_obj

                    meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&daily=temperature_2m_max,precipitation_probability_max,wind_speed_10m_max&start_date={friday.date()}&end_date={sunday.date()}"
                    weather_response = requests.get(meteo_url, timeout=15)

                    if weather_response.status_code == 200:
                        weather_data = weather_response.json()
                        daily = weather_data.get("daily", {})
                        temps = daily.get("temperature_2m_max", [])
                        rain_probs = daily.get("precipitation_probability_max", [])
                        wind_speeds = daily.get("wind_speed_10m_max", [])

                        if temps and len(temps) >= 3:
                            weather_message = "\n🌤️ *Hava proqnozu:*\n"
                            days = [
                                TRANSLATIONS["friday"],
                                TRANSLATIONS["saturday"],
                                TRANSLATIONS["sunday"],
                            ]
                            for i, day in enumerate(days):
                                if i < len(temps):
                                    temp = temps[i]
                                    rain = rain_probs[i] if i < len(rain_probs) else 0
                                    wind = wind_speeds[i] if i < len(wind_speeds) else 0
                                    rain_icon = (
                                        "🌧️" if rain >= 60 else "⛅" if rain >= 30 else "☀️"
                                    )
                                    weather_message += f"{day}: {temp:.1f}°C {rain_icon} {int(rain)}% 💨{wind:.1f}km/h\n"
                            message += weather_message
                            set_cached_data("weather", weather_message)
            except Exception as e:
                logger.error(f"Error fetching weather data: {e}")
                pass

        # Cache the complete result
        set_cached_data("next_race", message)
        return message
    except Exception as e:
        logger.error(f"Error in get_next_race: {e}")
        return TRANSLATIONS["error_fetching_race"].format(str(e))




# Global cache for API data to optimize Leapcell limits
# APIs update weekend-by-weekend, so long cache times are appropriate
CACHE = {
    "standings": {"data": None, "timestamp": None, "expiry": 86400},  # 24 hours (updates weekly)
    "constructor_standings": {"data": None, "timestamp": None, "expiry": 86400},  # 24 hours
    "last_session": {"data": None, "timestamp": None, "expiry": 604800},  # 1 week (results don't change)
    "next_race": {"data": None, "timestamp": None, "expiry": 86400},  # 24 hours
    "calendar": {"data": None, "timestamp": None, "expiry": 604800},  # 1 week (season schedule)
    "weather": {"data": None, "timestamp": None, "expiry": 21600},  # 6 hours
    "active_session": {"data": None, "timestamp": None, "expiry": 300},  # 5 minutes (for live checks)
    "live_session": {"data": None, "timestamp": None, "expiry": 30},  # 30 seconds (live session info)
}


def get_cached_data(cache_key):
    """Retrieve cached data if available and not expired"""
    cache_entry = CACHE.get(cache_key)
    if cache_entry and cache_entry["data"] and cache_entry["timestamp"]:
        now = datetime.now(ZoneInfo("UTC")).timestamp()
        if now - cache_entry["timestamp"] < cache_entry["expiry"]:
            return cache_entry["data"]
    return None


def set_cached_data(cache_key, data):
    """Cache data with current timestamp"""
    if cache_key in CACHE:
        CACHE[cache_key]["data"] = data
        CACHE[cache_key]["timestamp"] = datetime.now(ZoneInfo("UTC")).timestamp()


# Backward compatibility
def get_cached_calendar():
    return get_cached_data("calendar")


def set_cached_calendar(data):
    set_cached_data("calendar", data)


# ==================== LIVE TIMING ENHANCEMENTS ====================

def get_live_session_info():
    """Get current live session information"""
    try:
        cached = get_cached_data("live_session")
        if cached and cached.get('timestamp'):
            # Check if cache is still fresh (30 seconds)
            now = datetime.now(ZoneInfo("UTC")).timestamp()
            if now - cached['timestamp'] < 30:
                return cached

        logger.info("Fetching live session info from OpenF1 API")
        
        # Get current sessions
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year
        
        # Check current and next year for sessions
        years_to_check = [current_year]
        if now.month >= 11:
            years_to_check.append(current_year + 1)

        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=10)
                if sessions_response.status_code == 200:
                    sessions.extend(sessions_response.json())
            except Exception as e:
                logger.error(f"Error fetching sessions for year {year}: {e}")
                continue

        if not sessions:
            return None

        # Find the currently active session
        active_session = None
        for session in sessions:
            session_start = session.get("date_start")
            session_end = session.get("date_end")

            if session_start:
                try:
                    start_dt = datetime.fromisoformat(
                        session_start.replace("Z", "+00:00")
                    )
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))

                    time_diff_start = (start_dt - now).total_seconds() / 3600  # hours
                    time_diff_end = 0

                    if session_end:
                        end_dt = datetime.fromisoformat(
                            session_end.replace("Z", "+00:00")
                        )
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=ZoneInfo("UTC"))
                        time_diff_end = (end_dt - now).total_seconds() / 3600

                        # Session is active if it started within last 2 hours and hasn't ended + 1 hour grace period
                        if (
                            -2 <= time_diff_start <= 0 and time_diff_end > -1
                        ):
                            active_session = session
                            break
                    else:
                        # If no end time, check if session started recently (within 2 hours)
                        if (
                            -2 <= time_diff_start <= 1
                        ):
                            active_session = session
                            break
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing session times: {e}")
                    continue

        if not active_session:
            return None

        session_info = {
            'session': active_session,
            'session_key': active_session.get('session_key'),
            'session_name': active_session.get('session_name', 'F1 Session'),
            'meeting_name': active_session.get('meeting_name', 'Grand Prix'),
            'country_name': active_session.get('country_name', ''),
            'location': active_session.get('location', ''),
            'date_start': active_session.get('date_start'),
            'date_end': active_session.get('date_end'),
            'gmt_offset': active_session.get('gmt_offset'),
            'timestamp': now.timestamp()
        }

        # Cache the result
        set_cached_data("live_session", session_info)
        return session_info

    except Exception as e:
        logger.error(f"Error fetching live session info: {e}")
        return None


def get_live_positions(session_key):
    """Get current live positions for active session"""
    try:
        if not session_key:
            return []

        # Check cache first (15 seconds for live positions)
        cache_key = f"live_positions_{session_key}"
        cached = get_cached_data(cache_key)
        if cached and cached.get('timestamp'):
            now = datetime.now(ZoneInfo("UTC")).timestamp()
            if now - cached['timestamp'] < 15:
                return cached.get('positions', [])

        logger.info(f"Fetching live positions for session {session_key}")
        
        # Get current positions
        positions_url = f"https://api.openf1.org/v1/position?session_key={session_key}"
        positions_response = requests.get(positions_url, timeout=10)
        
        if positions_response.status_code != 200:
            return []

        positions_data = positions_response.json()
        if not positions_data:
            return []

        # Get driver info
        drivers_url = f"https://api.openf1.org/v1/drivers?session_key={session_key}"
        drivers_response = requests.get(drivers_url, timeout=10)
        drivers_info = {}
        
        if drivers_response.status_code == 200:
            for driver in drivers_response.json():
                driver_number = driver.get("driver_number")
                if driver_number:
                    drivers_info[driver_number] = {
                        'first_name': driver.get('first_name', ''),
                        'last_name': driver.get('last_name', ''),
                        'country_code': driver.get('country_code', ''),
                        'team_name': driver.get('team_name', '')
                    }

        # Process positions
        current_positions = {}
        for pos_entry in positions_data:
            driver_number = pos_entry.get("driver_number")
            position = pos_entry.get("position")
            date = pos_entry.get("date")

            if driver_number and position and date:
                if (
                    driver_number not in current_positions
                    or date > current_positions[driver_number]["date"]
                ):
                    driver_info = drivers_info.get(driver_number, {})
                    full_name = f"{driver_info.get('first_name', '')} {driver_info.get('last_name', '')}".strip()
                    
                    current_positions[driver_number] = {
                        "position": position,
                        "date": date,
                        "driver_number": driver_number,
                        "driver_name": full_name or f"Driver {driver_number}",
                        "country_code": driver_info.get('country_code', ''),
                        "team_name": driver_info.get('team_name', '')
                    }

        # Sort by position
        sorted_positions = sorted(
            current_positions.values(), 
            key=lambda x: int(x["position"]) if str(x["position"]).isdigit() else 999
        )

        # Cache the result
        cache_data = {
            'positions': sorted_positions,
            'timestamp': datetime.now(ZoneInfo("UTC")).timestamp()
        }
        set_cached_data(cache_key, cache_data)
        
        return sorted_positions

    except Exception as e:
        logger.error(f"Error fetching live positions: {e}")
        return []


def format_live_timing_message(session_info, positions):
    """Format live timing data into a nice message"""
    if not session_info:
        return TRANSLATIONS["live_not_available"]

    try:
        # Get session details
        session_name = session_info.get('session_name', 'F1 Session')
        meeting_name = session_info.get('meeting_name', 'Grand Prix')
        country_name = session_info.get('country_name', '')
        location = session_info.get('location', '')
        date_start = session_info.get('date_start')
        
        # Get flag emoji
        flag = get_country_flag(country_name)
        
        # Convert session start time to Baku time
        session_time_str = ""
        if date_start:
            try:
                start_dt = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))
                baku_time = start_dt.astimezone(ZoneInfo("Asia/Baku"))
                session_time_str = baku_time.strftime("%H:%M")
            except Exception:
                session_time_str = "Unknown"

        # Start building message
        message = f"🔴 *{flag} {meeting_name} {session_name}*\n\n"
        
        if location:
            message += f"{TRANSLATIONS['live_session_location']} {location}\n"
        
        if session_time_str:
            message += f"{TRANSLATIONS['live_session_time']} {session_time_str} (Bakı)\n"
        
        message += f"\n{TRANSLATIONS['live_positions_header']}\n"
        
        if not positions:
            message += f"{TRANSLATIONS['live_positions_loading']}\n"
        else:
            # Display top 15 positions
            for i, pos in enumerate(positions[:15]):
                try:
                    position = int(pos["position"])
                    driver_name = pos["driver_name"]
                    team_name = pos.get("team_name", "")
                    country_code = pos.get("country_code", "")
                    
                    driver_flag = get_country_flag(country_code)
                    
                    line = f"{position}. {driver_flag} {driver_name}"
                    if team_name:
                        line += f" ({team_name})"
                    
                    # Add winner indicator for position 1
                    if position == 1:
                        line += f" {TRANSLATIONS['live_position_winner']}"
                    
                    message += line + "\n"
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing position data: {e}")
                    continue

        # Add footer
        message += f"\n{TRANSLATIONS['live_update_frequency']}\n"
        message += f"{TRANSLATIONS['live_data_source']}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting live timing message: {e}")
        return TRANSLATIONS["error_occurred"].format(str(e))


def check_live_timing_available():
    """Check if live timing data is currently available"""
    try:
        session_info = get_live_session_info()
        if not session_info:
            return False, "Aktiv F1 sessiyası tapılmadı"
        
        session_key = session_info.get('session_key')
        if not session_key:
            return False, TRANSLATIONS["live_session_info_error"]
        
        positions = get_live_positions(session_key)
        if not positions:
            return False, TRANSLATIONS["live_positions_error"]
        
        return True, TRANSLATIONS["live_timing_available"]
        
    except Exception as e:
        logger.error(f"Error checking live timing availability: {e}")
        return False, "Live timing yoxlanılarkən xəta"


# ==================== PLAYWRIGHT F1 SCRAPER CLASS ====================

class F1TimingScraper:
    """F1 Timing Data Scraper using Playwright"""
    
    def __init__(self):
        self.base_url = "https://www.formula1.com/en/results"
        self.live_timing_url = "https://www.formula1.com/en/results/en/live"
        self.browser = None
        self.page = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_browser()
        
    async def start_browser(self):
        """Start Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available")
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            self.page = await self.browser.new_page()
            logger.info("Playwright browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
            
    async def close_browser(self):
        """Close Playwright browser"""
        try:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Playwright browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            
    async def scrape_live_timing_data(self):
        """Scrape live timing data from F1 official website"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        try:
            logger.info("Scraping live timing data...")
            await self.page.goto(self.live_timing_url, wait_until='networkidle', timeout=30000)
            
            # Wait for timing data to load
            await self.page.wait_for_selector('.timing-item, .driver-item, [class*="position"]', timeout=10000)
            
            # Extract driver positions and times
            drivers_data = await self.page.evaluate("""
                () => {
                    const drivers = [];
                    const driverElements = document.querySelectorAll('.timing-item, .driver-item, [class*="driver"], [class*="position"]');
                    
                    driverElements.forEach((element, index) => {
                        try {
                            const position = element.querySelector('[class*="position"], .position')?.textContent?.trim() || (index + 1).toString();
                            const driverName = element.querySelector('[class*="name"], .driver-name, .name')?.textContent?.trim() || 'Unknown';
                            const team = element.querySelector('[class*="team"], .team-name')?.textContent?.trim() || 'Unknown Team';
                            const lastLap = element.querySelector('[class*="lap"], .last-lap')?.textContent?.trim() || 'No time';
                            const gap = element.querySelector('[class*="gap"], .gap')?.textContent?.trim() || '+0.000';
                            
                            if (position && driverName) {
                                drivers.push({
                                    position: position,
                                    driver: driverName,
                                    team: team,
                                    lastLap: lastLap,
                                    gap: gap
                                });
                            }
                        } catch (e) {
                            console.warn('Error parsing driver element:', e);
                        }
                    });
                    
                    return drivers;
                }
            """)
            
            # Also try to get session info
            session_info = await self.page.evaluate("""
                () => {
                    const title = document.title;
                    const sessionName = title.split('|')[0]?.trim() || 'F1 Live Timing';
                    
                    // Try to find session time
                    const timeElement = document.querySelector('.session-time, .current-time, [class*="time"]');
                    const currentTime = timeElement?.textContent?.trim() || '';
                    
                    // Try to find session status
                    const statusElement = document.querySelector('.session-status, .status, [class*="status"]');
                    const status = statusElement?.textContent?.trim() || 'Running';
                    
                    return {
                        sessionName: sessionName,
                        currentTime: currentTime,
                        status: status
                    };
                }
            """)
            
            logger.info(f"Scraped {len(drivers_data)} drivers from live timing")
            
            return {
                'session_info': session_info,
                'drivers': drivers_data,
                'timestamp': datetime.now(ZoneInfo("UTC")).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping live timing data: {e}")
            return {
                'error': str(e),
                'session_info': {'sessionName': 'Error', 'currentTime': '', 'status': 'Failed'},
                'drivers': [],
                'timestamp': datetime.now(ZoneInfo("UTC")).isoformat()
            }
    
    async def scrape_race_results(self, year=None, race=None):
        """Scrape race results for specific year and race"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
            
        try:
            # Build URL for specific race results
            if year and race:
                url = f"{self.base_url}/{year}/races/{race}"
            else:
                url = self.base_url
                
            logger.info(f"Scraping race results from: {url}")
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for results table
            await self.page.wait_for_selector('table, .results, [class*="results"]', timeout=15000)
            
            # Extract race results
            results = await self.page.evaluate("""
                () => {
                    const results = [];
                    const rows = document.querySelectorAll('table tr, .results .result, [class*="result"]');
                    
                    rows.forEach((row, index) => {
                        try {
                            // Skip header rows
                            if (row.tagName === 'THEAD' || row.querySelector('th')) return;
                            
                            const cells = row.querySelectorAll('td, .cell');
                            if (cells.length >= 3) {
                                const position = cells[0]?.textContent?.trim() || (index).toString();
                                const driver = cells[1]?.textContent?.trim() || 'Unknown';
                                const team = cells[2]?.textContent?.trim() || 'Unknown Team';
                                const time = cells[3]?.textContent?.trim() || 'No time';
                                const points = cells[4]?.textContent?.trim() || '0';
                                
                                if (position && driver) {
                                    results.push({
                                        position: position,
                                        driver: driver,
                                        team: team,
                                        time: time,
                                        points: points
                                    });
                                }
                            }
                        } catch (e) {
                            console.warn('Error parsing result row:', e);
                        }
                    });
                    
                    return results;
                }
            """)
            
            logger.info(f"Scraped {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error scraping race results: {e}")
            return []

# ==================== TELEGRAM BOT HANDLERS ====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with comprehensive inline keyboard"""
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} started the bot")
    else:
        logger.info("User started the bot (unknown user)")
    keyboard = [
        [
            InlineKeyboardButton(
                TRANSLATIONS["driver_standings"], callback_data="standings"
            ),
            InlineKeyboardButton(
                TRANSLATIONS["constructor_standings"], callback_data="constructors"
            ),
        ],
        [
            InlineKeyboardButton(
                TRANSLATIONS["last_session"], callback_data="lastrace"
            ),
            InlineKeyboardButton(
                TRANSLATIONS["schedule_weather"], callback_data="nextrace"
            ),
        ],
        [
            InlineKeyboardButton(TRANSLATIONS["live_timing"], callback_data="live"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""{TRANSLATIONS["welcome_title"]}
    
{TRANSLATIONS["welcome_text"]}"""

    if isinstance(update.message, Message):
        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu buttons"""
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested menu")
    else:
        logger.info("User requested menu (unknown user)")
    keyboard = [
        [
            InlineKeyboardButton(
                TRANSLATIONS["driver_standings"], callback_data="standings"
            ),
            InlineKeyboardButton(
                TRANSLATIONS["constructor_standings"], callback_data="constructors"
            ),
        ],
        [
            InlineKeyboardButton(
                TRANSLATIONS["last_session"], callback_data="lastrace"
            ),
            InlineKeyboardButton(
                TRANSLATIONS["schedule_weather"], callback_data="nextrace"
            ),
        ],
        [
            InlineKeyboardButton(TRANSLATIONS["live_timing"], callback_data="live"),
        ],
        [
            InlineKeyboardButton(
                TRANSLATIONS["help_commands_btn"], callback_data="help"
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update.message, Message):
        await update.message.reply_text(
            f"{TRANSLATIONS['menu_title']}\n\n{TRANSLATIONS['menu_text']}",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    if query is None:
        return
    
    await query.answer()
    logger.info(f"User {query.from_user.id} clicked button: {query.data}")

    try:
        if query.data == "standings":
            message = get_current_standings()
        elif query.data == "constructors":
            message = get_constructor_standings()
        elif query.data == "lastrace":
            message = get_last_session_results()
        elif query.data == "nextrace":
            message = get_next_race()
            # Add button to view full calendar
            schedule_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Tam Mövsüm Cədvəlini Gör", callback_data="calendar")],
                [InlineKeyboardButton("🏠 Ana Menyuya Qayıt", callback_data="back_to_menu")]
            ])
            if isinstance(query.message, Message):
                try:
                    await query.edit_message_text(
                        message,
                        parse_mode="Markdown",
                        reply_markup=schedule_keyboard
                    )
                except Exception as e:
                    logger.warning(f"Could not edit message, sending new: {e}")
                    await query.message.reply_text(
                        message,
                        parse_mode="Markdown",
                        reply_markup=schedule_keyboard
                    )
            return
        elif query.data == "calendar":
            # Fetch and display the F1 season calendar
            cached_data = get_cached_calendar()
            if cached_data:
                message = cached_data
            else:
                message = get_f1_season_calendar()
                set_cached_calendar(message)
        elif query.data == "live_refresh":
            # Refresh live timing data using Playwright
            try:
                from f1_playwright_scraper import get_optimized_live_timing, format_timing_data_for_telegram

                live_data = await get_optimized_live_timing()
                if not live_data:
                    message = "❌ Canlı vaxt məlumatları mövcud deyil\n\nℹ️ Playwright quraşdırmaq üçün: pip install playwright && playwright install chromium"
                else:
                    message = format_timing_data_for_telegram(live_data)

                    # Add refresh button again
                    keyboard = [
                        [InlineKeyboardButton(TRANSLATIONS["live_refresh_button"], callback_data="live_refresh")],
                        [InlineKeyboardButton("🏠 Ana Menyuya Qayıt", callback_data="back_to_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    if isinstance(query.message, Message):
                        try:
                            await query.edit_message_text(
                                message,
                                parse_mode="Markdown",
                                reply_markup=reply_markup
                            )
                        except Exception as e:
                            logger.warning(f"Could not edit message, sending new: {e}")
                            await query.message.reply_text(
                                message,
                                parse_mode="Markdown",
                                reply_markup=reply_markup
                            )
                    return
            except Exception as e:
                logger.error(f"Error refreshing live data: {e}")
                message = f"❌ Xəta: {str(e)}\n\nℹ️ Playwright quraşdırmaq üçün: pip install playwright && playwright install chromium"
        elif query.data == "live":
            # Start live timing with Playwright scraper
            message = "🔴 Canlı vaxt yüklənir...\n\n⏳ Formula-timer.com saytından məlumatlar alınır..."
        elif query.data == "help":
            message = """ℹ️ *F1 Bot Köməyi*

Bu bot Formula 1 yarışları haqqında məlumat verir.

*Əmrlər:*
/start - Botu başlat
/menu - Əsas menyunu göstər
/standings - Sürücü sıralamaları
/constructors - Konstruktor sıralamaları
/lastrace - Son sessiya nəticələri
/nextrace - Gələn yarış cədvəli
/live - Canlı vaxt (aktiv sessiya zamanı)

*Qeyd:* Bütün vaxtlar Bakı vaxtı ilə göstərilir."""
        elif query.data == "back_to_menu":
            # Return to main menu
            keyboard = [
                [
                    InlineKeyboardButton(
                        TRANSLATIONS["driver_standings"], callback_data="standings"
                    ),
                    InlineKeyboardButton(
                        TRANSLATIONS["constructor_standings"], callback_data="constructors"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        TRANSLATIONS["last_session"], callback_data="lastrace"
                    ),
                    InlineKeyboardButton(
                        TRANSLATIONS["schedule_weather"], callback_data="nextrace"
                    ),
                ],
                [
                    InlineKeyboardButton(TRANSLATIONS["live_timing"], callback_data="live"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"{TRANSLATIONS['menu_title']}\n\n{TRANSLATIONS['menu_text']}"
            # For menu, use the full keyboard instead of back button
            if isinstance(query.message, Message):
                try:
                    await query.edit_message_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"Could not edit message, sending new: {e}")
                    await query.message.reply_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
            return  # Don't add back button for menu
        else:
            message = TRANSLATIONS["unknown_command"]
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        message = TRANSLATIONS["error_occurred"].format(str(e))

    # Create a back button for navigation
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Ana Menyuya Qayıt", callback_data="back_to_menu")]
    ])

    # Edit the original message with the result and back button
    if isinstance(query.message, Message):
        try:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=back_keyboard
            )
        except Exception as e:
            # Fallback to sending a new message if edit fails
            logger.warning(f"Could not edit message, sending new: {e}")
            await query.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=back_keyboard
            )


# Command handlers
async def standings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested standings")
    else:
        logger.info("User requested standings (unknown user)")
    if isinstance(update.message, Message):
        await update.message.reply_text(TRANSLATIONS["loading"])
        message = get_current_standings()
        await update.message.reply_text(message, parse_mode="Markdown")


async def constructors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested constructor standings")
    else:
        logger.info("User requested constructor standings (unknown user)")
    if isinstance(update.message, Message):
        await update.message.reply_text(TRANSLATIONS["loading"])
        message = get_constructor_standings()
        await update.message.reply_text(message, parse_mode="Markdown")


async def lastrace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested last race results")
    else:
        logger.info("User requested last race results (unknown user)")
    if isinstance(update.message, Message):
        await update.message.reply_text(TRANSLATIONS["loading"])
        message = get_last_session_results()
        await update.message.reply_text(message, parse_mode="Markdown")


async def nextrace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested next race")
    else:
        logger.info("User requested next race (unknown user)")
    if isinstance(update.message, Message):
        await update.message.reply_text(TRANSLATIONS["loading"])
        message = get_next_race()
        await update.message.reply_text(message, parse_mode="Markdown")


async def live_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live timing using Playwright scraper from formula-timer.com"""
    if update.effective_user:
        logger.info(f"User {update.effective_user.id} requested live timing")
    else:
        logger.info("User requested live timing (unknown user)")
    if isinstance(update.message, Message):
        loading_msg = await update.message.reply_text(
            "🔴 Canlı vaxt məlumatları yüklənir...\n\n⏳ Formula-timer.com saytından məlumatlar alınır..."
        )

        try:
            # Import the Playwright scraper
            from f1_playwright_scraper import get_optimized_live_timing, format_timing_data_for_telegram

            # Get live timing data using Playwright
            live_data = await get_optimized_live_timing()

            if not live_data:
                await loading_msg.edit_text(
                    "❌ Canlı vaxt məlumatları mövcud deyil\n\n🔴 Canlı vaxt yalnız F1 yarış həftəsonlarında mövcuddur.\n\n📊 Canlı vaxt göstərir:\n• Sürücülərin mövqeləri\n• Interval vaxtları\n• Ən yaxşı dövrə vaxtları\n• Təkər məlumatları\n• Hər çağırışda yenilənən məlumatlar\n\nAlternativlər:\n• /nextrace - Gələn yarış və hava proqnozu\n• /lastrace - Son sessiya nəticələri\n\nℹ️ Playwright quraşdırmaq üçün: pip install playwright && playwright install chromium"
                )
                return

            # Format the data for Telegram
            live_message = format_timing_data_for_telegram(live_data)

            # Add a refresh button for users
            keyboard = [
                [InlineKeyboardButton(TRANSLATIONS["live_refresh_button"], callback_data="live_refresh")],
                [InlineKeyboardButton("🏠 Ana Menyuya Qayıt", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await loading_msg.edit_text(
                live_message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error in live_cmd: {e}")
            await loading_msg.edit_text(
                f"❌ Xəta: {str(e)}\n\nℹ️ Playwright quraşdırmaq üçün: pip install playwright && playwright install chromium"
            )










