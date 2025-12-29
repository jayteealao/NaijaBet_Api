#!/usr/bin/env python3
"""
Complete example of using Betking with Playwright browser automation.

This example shows how to:
1. Use Betking with Playwright to bypass Cloudflare
2. Fetch odds from various leagues
3. Compare odds from multiple bookmakers
4. Handle errors gracefully

Requirements:
    pip install playwright
    playwright install chromium

Author: NaijaBet API
"""

from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
from NaijaBet_Api.bookmakers.bet9ja import Bet9ja
from NaijaBet_Api.bookmakers.nairabet import Nairabet
from NaijaBet_Api.id import Betid
import json


def example_1_basic_usage():
    """Example 1: Basic usage with context manager"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Betking Playwright Usage")
    print("=" * 80)

    try:
        # Use context manager - browser automatically closes when done
        with BetkingPlaywright(headless=True) as betking:
            # Fetch Premier League odds
            print("\n📡 Fetching Premier League odds...")
            data = betking.get_league(Betid.PREMIERLEAGUE)

            print(f"✅ Retrieved {len(data)} matches")

            if data:
                # Display first match
                print(f"\n📋 First match:")
                print(f"   {data[0]['match']}")
                print(f"   Home: {data[0].get('home')} | Draw: {data[0].get('draw')} | Away: {data[0].get('away')}")

                # Display all matches
                print(f"\n📋 All Premier League matches:")
                for i, match in enumerate(data, 1):
                    print(f"   {i}. {match['match']}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_multiple_leagues():
    """Example 2: Fetching multiple leagues"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Fetching Multiple Leagues")
    print("=" * 80)

    try:
        with BetkingPlaywright(headless=True) as betking:
            leagues = [
                (Betid.PREMIERLEAGUE, "Premier League"),
                (Betid.LALIGA, "La Liga"),
                (Betid.BUNDESLIGA, "Bundesliga"),
                (Betid.SERIEA, "Serie A"),
            ]

            for league_id, league_name in leagues:
                print(f"\n📡 Fetching {league_name}...")
                data = betking.get_league(league_id)
                print(f"   ✅ {len(data)} matches")

                if data:
                    print(f"   First match: {data[0]['match']}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_team_search():
    """Example 3: Search for specific team"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Team Search")
    print("=" * 80)

    try:
        with BetkingPlaywright(headless=True) as betking:
            teams = ["Manchester", "Arsenal", "Liverpool"]

            for team in teams:
                print(f"\n🔍 Searching for {team}...")
                matches = betking.get_team(team)

                print(f"   ✅ Found {len(matches)} matches")
                for match in matches:
                    print(f"      {match['match']}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_compare_bookmakers():
    """Example 4: Compare odds across bookmakers"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Compare Odds Across Bookmakers")
    print("=" * 80)

    try:
        # Initialize all bookmakers
        bet9ja = Bet9ja()
        nairabet = Nairabet()

        # Betking with Playwright
        with BetkingPlaywright(headless=True) as betking:
            print("\n📡 Fetching odds from all bookmakers...")

            # Get Premier League from all
            bet9ja_data = bet9ja.get_league(Betid.PREMIERLEAGUE)
            nairabet_data = nairabet.get_league(Betid.PREMIERLEAGUE)
            betking_data = betking.get_league(Betid.PREMIERLEAGUE)

            print(f"\nResults:")
            print(f"   Bet9ja: {len(bet9ja_data)} matches")
            print(f"   Nairabet: {len(nairabet_data)} matches")
            print(f"   Betking (Playwright): {len(betking_data)} matches")

            # Compare odds for first match
            if bet9ja_data and nairabet_data and betking_data:
                print(f"\n📊 Odds comparison for: {bet9ja_data[0]['match']}")
                print(f"   Bet9ja:    {bet9ja_data[0].get('home')} / {bet9ja_data[0].get('draw')} / {bet9ja_data[0].get('away')}")
                print(f"   Nairabet:  {nairabet_data[0].get('home')} / {nairabet_data[0].get('draw')} / {nairabet_data[0].get('away')}")
                print(f"   Betking:   {betking_data[0].get('home')} / {betking_data[0].get('draw')} / {betking_data[0].get('away')}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_5_manual_management():
    """Example 5: Manual browser management"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Manual Browser Management")
    print("=" * 80)

    betking = None
    try:
        # Create instance
        betking = BetkingPlaywright(headless=True, timeout=60000)

        # Manually start browser
        print("🚀 Starting browser...")
        betking._start_browser()

        # Fetch data
        print("📡 Fetching data...")
        data = betking.get_league(Betid.PREMIERLEAGUE)
        print(f"✅ Got {len(data)} matches")

        # Can fetch more without restarting browser
        data2 = betking.get_league(Betid.LALIGA)
        print(f"✅ Got {len(data2)} more matches from La Liga")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        # Manually stop browser
        if betking:
            print("🛑 Stopping browser...")
            betking._stop_browser()


def example_6_get_all_leagues():
    """Example 6: Get all leagues at once"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Get All Leagues")
    print("=" * 80)

    try:
        with BetkingPlaywright(headless=True) as betking:
            print("📡 Fetching ALL leagues...")
            all_data = betking.get_all()

            print(f"✅ Retrieved {len(all_data)} total matches")

            # Group by league
            leagues = {}
            for match in all_data:
                league = match.get('league', 'Unknown')
                if league not in leagues:
                    leagues[league] = []
                leagues[league].append(match)

            print(f"\n📊 Matches by league:")
            for league, matches in leagues.items():
                print(f"   {league}: {len(matches)} matches")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_7_error_handling():
    """Example 7: Robust error handling"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Robust Error Handling")
    print("=" * 80)

    def fetch_with_retry(betking, league, max_retries=3):
        """Fetch with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                data = betking.get_league(league)
                return data
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                if attempt == max_retries - 1:
                    print(f"   ❌ Failed after {max_retries} attempts")
                    return []
        return []

    try:
        with BetkingPlaywright(headless=True) as betking:
            print("\n📡 Fetching with retry logic...")
            data = fetch_with_retry(betking, Betid.PREMIERLEAGUE)
            print(f"✅ Final result: {len(data)} matches")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  BETKING PLAYWRIGHT INTEGRATION EXAMPLES                     ║
║                                                                              ║
║  This demonstrates how to use Betking with Playwright browser automation    ║
║  to bypass Cloudflare bot protection.                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Multiple Leagues", example_2_multiple_leagues),
        ("Team Search", example_3_team_search),
        ("Compare Bookmakers", example_4_compare_bookmakers),
        ("Manual Management", example_5_manual_management),
        ("Get All Leagues", example_6_get_all_leagues),
        ("Error Handling", example_7_error_handling),
    ]

    for name, example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")

    print("\n" + "=" * 80)
    print("✅ Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
