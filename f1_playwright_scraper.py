import asyncio
import logging
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class OptimizedLiveTimingScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None

    async def initialize(self):
        """Initialize browser once and keep it alive"""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().__aenter__()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = await self.context.new_page()

            logging.info("Loading formula-timer.com live timing (one time)...")
            await self.page.goto('https://formula-timer.com/livetiming', wait_until='domcontentloaded')
            await self.page.wait_for_timeout(3000)

            return True
        except Exception as e:
            logging.error(f"Failed to initialize browser: {e}")
            return False

    async def get_live_data(self):
        """Get current data without reloading page"""
        try:
            if not self.page:
                return None

            # Just read current DOM - no reload!
            content = await self.page.content()
            soup = BeautifulSoup(content, "html.parser")

            session_info = self._extract_session_info(soup)
            timing_data = self._extract_timing_data(soup)
            race_control = self._extract_race_control_messages(soup)

            return {
                "session": session_info,
                "timing": timing_data,
                "race_control": race_control[:5] if race_control else []
            }

        except Exception as e:
            logging.error(f"Error getting live data: {e}")
            return None

    def _extract_session_info(self, soup):
        """Extract current session information"""
        try:
            session_title = soup.find('h1')
            if session_title:
                session_text = session_title.get_text(strip=True)
                return {"name": session_text}
        except:
            pass
        return {"name": "Unknown Session"}

    def _extract_timing_data(self, soup):
        """Extract live timing data from the main timing table"""
        timing_data = []

        try:
            timing_table = soup.find('table', class_='table-auto')
            if not timing_table:
                return timing_data

            tbody = timing_table.find('tbody')
            if not tbody:
                return timing_data

            rows = tbody.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue

                try:
                    driver_cell = cells[0]
                    position_elem = driver_cell.find('p', class_='font-bold')
                    position = position_elem.get_text(strip=True) if position_elem else "N/A"

                    driver_tags = driver_cell.find_all('p')
                    driver_code = "N/A"
                    for tag in driver_tags:
                        text = tag.get_text(strip=True)
                        if len(text) == 3 and text.isupper():
                            driver_code = text
                            break

                    interval_cell = cells[4] if len(cells) > 4 else cells[1]
                    interval = interval_cell.get_text(strip=True)

                    tyre_cell = cells[2]
                    tyre_age = tyre_cell.find('p')
                    tyre_age_text = tyre_age.get_text(strip=True) if tyre_age else "N/A"

                    tyre_compound = "N/A"
                    tyre_img = tyre_cell.find('img')
                    if tyre_img and tyre_img.get('src'):
                        src = tyre_img.get('src')
                        if 'soft' in src.lower():
                            tyre_compound = "S🔴"
                        elif 'medium' in src.lower():
                            tyre_compound = "M🟡"
                        elif 'hard' in src.lower():
                            tyre_compound = "H⚪"
                        elif 'intermediate' in src.lower() or 'inter' in src.lower():
                            tyre_compound = "I🟢"
                        elif 'wet' in src.lower():
                            tyre_compound = "W🔵"

                    best_lap_cell = cells[3]
                    best_lap = best_lap_cell.get_text(strip=True)

                    gap = cells[1].get_text(strip=True) if len(cells) > 1 else "N/A"
                    last_lap = cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"

                    timing_data.append({
                        "position": position,
                        "driver": driver_code,
                        "interval": interval,
                        "best_lap": best_lap,
                        "last_lap": last_lap,
                        "gap": gap,
                        "tyre_age": tyre_age_text,
                        "tyre_compound": tyre_compound
                    })

                except Exception as e:
                    logging.debug(f"Error parsing row: {e}")
                    continue

        except Exception as e:
            logging.error(f"Error extracting timing data: {e}")

        return timing_data

    def _extract_race_control_messages(self, soup):
        """Extract race control messages"""
        messages = []

        try:
            message_tables = soup.find_all('table')

            for table in message_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        time_elem = cells[0].find('time')
                        message_elem = cells[1].find('p')

                        if time_elem and message_elem:
                            time_text = time_elem.get_text(strip=True)
                            message_text = message_elem.get_text(strip=True)

                            if message_text and len(message_text) > 10:
                                messages.append({
                                    "time": time_text,
                                    "message": message_text
                                })
        except:
            pass

        return messages

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.__aexit__(None, None, None)
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

def format_timing_data_for_telegram(data):
    """Format the scraped data for Telegram bot display"""
    if not data:
        return "❌ No live timing data available"

    session = data.get('session', {})
    timing = data.get('timing', [])

    message = f"🏁 {session.get('name', 'F1 Session')}\n\n"

    if timing:
        message += "🏎️ Live Timing:\n"
        for driver in timing:
            pos = driver.get('position', 'N/A')
            name = driver.get('driver', 'N/A')
            interval = driver.get('interval', 'N/A')
            best_lap = driver.get('best_lap', 'N/A')
            tyre = driver.get('tyre_compound', 'N/A')

            message += f"P{pos}: {name} | {interval} | {best_lap} | {tyre}\n"
    else:
        message += "⚠️ No timing data available - session may not be active\n"

    now = datetime.now()
    message += f"\n🕐 Last update: {now.strftime('%H:%M:%S')}"

    return message

# Global scraper instance
_scraper_instance = None

async def get_optimized_live_timing():
    """Get live timing data using optimized scraper"""
    global _scraper_instance

    try:
        if _scraper_instance is None:
            _scraper_instance = OptimizedLiveTimingScraper()
            if not await _scraper_instance.initialize():
                return None

        return await _scraper_instance.get_live_data()

    except Exception as e:
        logging.error(f"Error in optimized live timing: {e}")
        # Reset instance on error
        if _scraper_instance:
            await _scraper_instance.cleanup()
            _scraper_instance = None
        return None

async def cleanup_optimized_scraper():
    """Cleanup the global scraper instance"""
    global _scraper_instance
    if _scraper_instance:
        await _scraper_instance.cleanup()
        _scraper_instance = None

async def main():
    """Test the optimized scraper"""
    print("🏎️ Testing Optimized Formula-Timer.com Live Timing Scraper")
    print("=" * 60)

    scraper = OptimizedLiveTimingScraper()

    if await scraper.initialize():
        print("✅ Browser initialized successfully!")

        # Test multiple data fetches without reloading
        for i in range(3):
            print(f"\n📊 Fetch #{i+1}:")
            data = await scraper.get_live_data()

            if data:
                print(f"  Session: {data['session']['name']}")
                print(f"  Timing entries: {len(data['timing'])}")
                print(f"  Race control messages: {len(data['race_control'])}")
            else:
                print("  ❌ No data received")

            if i < 2:  # Don't sleep after last iteration
                await asyncio.sleep(5)

        await scraper.cleanup()
        print("\n✅ Test completed successfully!")
    else:
        print("❌ Failed to initialize browser")

if __name__ == "__main__":
    asyncio.run(main())