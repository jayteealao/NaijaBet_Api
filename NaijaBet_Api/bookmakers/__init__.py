"""Bookmakers module

Available bookmakers:
- Bet9ja: Full support, no browser automation needed
- Betking: Standard version (Cloudflare blocked), Playwright version available
- Nairabet: Full support, no browser automation needed
"""

from .bet9ja import Bet9ja
from .betking import Betking
from .nairabet import Nairabet

# Playwright version (optional - only if playwright installed)
try:
    from .betking_playwright import BetkingPlaywright
    __all__ = ['Bet9ja', 'Betking', 'Nairabet', 'BetkingPlaywright']
except ImportError:
    __all__ = ['Bet9ja', 'Betking', 'Nairabet']
