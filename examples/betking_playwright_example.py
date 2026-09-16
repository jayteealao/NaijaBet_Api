#!/usr/bin/env python3
"""
Examples for BetkingPlaywright, the browser-driven Betking client.

Plain ``Betking`` works over HTTP requests from a Nigerian egress. From another egress the
Betking API answers 403 and the library raises ``BookmakerBlockedError``; ``BetkingPlaywright``
fetches through a Chromium page instead. This example shows how to:
1. Use BetkingPlaywright with the context manager
2. Fetch odds from several leagues
3. Compare odds with Bet9ja and Nairabet
4. Handle the typed exceptions

Requirements:
    pip install "NaijaBet_Api[playwright]"
    playwright install chromium
"""

from NaijaBet_Api.bookmakers.bet9ja import Bet9ja
from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
from NaijaBet_Api.bookmakers.nairabet import Nairabet
from NaijaBet_Api.exceptions import BookmakerBlockedError, BookmakerTimeoutError, NaijaBetError
from NaijaBet_Api.id import Betid


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
                print("\n📋 First match:")
                print(f"   {data[0]['match']}")
                print(f"   Home: {data[0].get('home')} | Draw: {data[0].get('draw')} | Away: {data[0].get('away')}")

                # Display all matches
                print("\n📋 All Premier League matches:")
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

            print("\nResults:")
            print(f"   Bet9ja: {len(bet9ja_data)} matches")
            print(f"   Nairabet: {len(nairabet_data)} matches")
            print(f"   Betking (Playwright): {len(betking_data)} matches")

            # Compare odds for first match
            if bet9ja_data and nairabet_data and betking_data:
                print(f"\n📊 Odds comparison for: {bet9ja_data[0]['match']}")
                odds = bet9ja_data[0]
                print(f"   Bet9ja:    {odds.get('home')} / {odds.get('draw')} / {odds.get('away')}")
                odds = nairabet_data[0]
                print(f"   Nairabet:  {odds.get('home')} / {odds.get('draw')} / {odds.get('away')}")
                odds = betking_data[0]
                print(f"   Betking:   {odds.get('home')} / {odds.get('draw')} / {odds.get('away')}")

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
                league = match.get("league", "Unknown")
                if league not in leagues:
                    leagues[league] = []
                leagues[league].append(match)

            print("\n📊 Matches by league:")
            for league, matches in leagues.items():
                print(f"   {league}: {len(matches)} matches")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_7_error_handling():
    """Example 7: Typed exceptions: retry a timeout, stop on a block"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Error Handling")
    print("=" * 80)

    def fetch_with_retry(betking, league, max_retries=3):
        """Retry a timeout; a block or any other failure propagates to the caller."""
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...")
                return betking.get_league(league)
            except BookmakerTimeoutError as exc:
                print(f"   Timed out: {exc}")
        raise BookmakerTimeoutError("betking", f"timed out on all {max_retries} attempts")

    try:
        with BetkingPlaywright(headless=True) as betking:
            print("\nFetching with retry logic...")
            data = fetch_with_retry(betking, Betid.PREMIERLEAGUE)
            print(f"Final result: {len(data)} matches")

    except BookmakerBlockedError as exc:
        print(f"Blocked ({exc.wall}, HTTP {exc.status}); a Nigerian egress is required")
    except NaijaBetError as exc:
        print(f"Error: {exc}")


def main():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  BETKING PLAYWRIGHT INTEGRATION EXAMPLES                     ║
║                                                                              ║
║  This demonstrates BetkingPlaywright, the browser-driven Betking client      ║
║  for an egress that the Betking API denies.                                 ║
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
