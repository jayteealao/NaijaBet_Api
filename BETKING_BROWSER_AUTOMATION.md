# Accessing Betking API with Browser Automation

Since Betking's API is protected by Cloudflare bot detection, you need to use browser automation to access it in production.

## Why Browser Automation?

Betking uses Cloudflare's enterprise bot protection which blocks:
- Python `requests` library
- `curl` and similar command-line tools
- Any automated script without a real browser

The solution is to use a real browser (via Playwright or Selenium) that passes Cloudflare's checks.

## Solution 1: Playwright (Recommended)

### Installation
```bash
pip install playwright
playwright install chromium
```

### Complete Example
```python
from playwright.sync_api import sync_playwright
import requests
import json

def get_betking_data_with_browser():
    """
    Use Playwright to get past Cloudflare and fetch Betking data
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Visit main site to establish session
        print("Loading Betking site...")
        page.goto("https://betking.com/sports")
        page.wait_for_load_state("networkidle")

        # Now fetch the API endpoint using the browser
        api_url = "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/en/4/841/0/0"

        response = page.request.get(api_url)
        data = response.json()

        browser.close()

        return data

# Use it
if __name__ == "__main__":
    data = get_betking_data_with_browser()
    print(f"Got {len(data)} matches")
    print(json.dumps(data[0], indent=2))
```

### Integration with NaijaBet_Api
```python
from playwright.sync_api import sync_playwright
from NaijaBet_Api.bookmakers.betking import Betking
from NaijaBet_Api.id import Betid
import requests

class BetkingWithBrowser(Betking):
    """
    Enhanced Betking class that uses browser automation
    """

    def __init__(self):
        # Don't call parent init - we'll manage session differently
        self.site = self._site
        self.session = requests.Session()
        self._setup_browser_session()

    def _setup_browser_session(self):
        """Set up session with cookies from browser"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Visit site to get cookies
            page.goto("https://betking.com/sports")
            page.wait_for_load_state("networkidle")

            # Extract cookies
            cookies = context.cookies()
            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', '')
                )

            browser.close()

    def get_league_with_browser(self, league: Betid):
        """Get league data using browser automation"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to site
            page.goto("https://betking.com/sports")
            page.wait_for_load_state("networkidle")

            # Fetch API using browser context
            api_url = league.to_endpoint(self.site)
            response = page.request.get(api_url)

            try:
                data = response.json()
                browser.close()
                return self.normalizer(data)
            except Exception as e:
                print(f"Error: {e}")
                browser.close()
                return []

# Usage
betking = BetkingWithBrowser()
data = betking.get_league_with_browser(Betid.PREMIERLEAGUE)
print(f"Got {len(data)} matches")
```

## Solution 2: Selenium

### Installation
```bash
pip install selenium
# Download ChromeDriver from https://chromedriver.chromium.org/
```

### Example
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import requests

def get_betking_with_selenium():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Launch browser
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Visit site
        driver.get("https://betking.com/sports")
        time.sleep(5)  # Wait for Cloudflare check

        # Get cookies
        cookies = driver.get_cookies()

        # Create session with cookies
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        # Now use session to fetch API
        api_url = "https://sportsapicdn-desktop.betking.com/api/feeds/prematch/en/4/841/0/0"
        response = session.get(api_url)

        return response.json()

    finally:
        driver.quit()

# Usage
data = get_betking_with_selenium()
```

## Solution 3: Use Alternative Bookmakers

Since Bet9ja and Nairabet have accessible APIs, consider using them instead:

```python
from NaijaBet_Api.bookmakers.bet9ja import Bet9ja
from NaijaBet_Api.bookmakers.nairabet import Nairabet
from NaijaBet_Api.id import Betid

# These work perfectly without browser automation
bet9ja = Bet9ja()
nairabet = Nairabet()

# Get data from multiple sources
bet9ja_odds = bet9ja.get_league(Betid.PREMIERLEAGUE)
nairabet_odds = nairabet.get_league(Betid.PREMIERLEAGUE)

print(f"Bet9ja: {len(bet9ja_odds)} matches")
print(f"Nairabet: {len(nairabet_odds)} matches")
```

## Performance Considerations

### Browser Automation
- **Pros**: Works reliably, bypasses Cloudflare
- **Cons**: Slower (1-5 seconds per request), more resource intensive

### When to Use Each Approach

1. **Use Bet9ja/Nairabet** for:
   - Real-time data needs
   - High-frequency requests
   - Production APIs
   - Lower resource usage

2. **Use Betking with browser** for:
   - Complete market coverage (when you need all three)
   - Data comparison across bookmakers
   - Occasional requests
   - When you specifically need Betking's odds

## Best Practice: Multi-Provider Setup

```python
from NaijaBet_Api.bookmakers.bet9ja import Bet9ja
from NaijaBet_Api.bookmakers.nairabet import Nairabet
from NaijaBet_Api.id import Betid

class OddsAggregator:
    """Aggregate odds from multiple providers"""

    def __init__(self):
        self.bet9ja = Bet9ja()
        self.nairabet = Nairabet()
        # Don't include Betking unless you set up browser automation

    def get_best_odds(self, league: Betid):
        """Get odds from all available providers"""
        all_odds = []

        # Bet9ja (fast, reliable)
        try:
            bet9ja_data = self.bet9ja.get_league(league)
            all_odds.extend(bet9ja_data)
        except Exception as e:
            print(f"Bet9ja error: {e}")

        # Nairabet (fast, reliable)
        try:
            nairabet_data = self.nairabet.get_league(league)
            all_odds.extend(nairabet_data)
        except Exception as e:
            print(f"Nairabet error: {e}")

        # Optionally add Betking with browser automation here
        # betking_data = self.betking_with_browser.get_league(league)

        return all_odds

# Usage
aggregator = OddsAggregator()
all_odds = aggregator.get_best_odds(Betid.PREMIERLEAGUE)
print(f"Total matches from all providers: {len(all_odds)}")
```

## Conclusion

For production use:
- ✅ **Bet9ja and Nairabet**: Use directly (no browser needed)
- ⚠️ **Betking**: Requires browser automation (Playwright/Selenium)
- 🎯 **Best approach**: Use multiple providers for reliability
