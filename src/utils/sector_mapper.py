"""
Sector code mapping utility
Maps KIS sector codes to Korean sector names
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from loguru import logger

class SectorMapper:
    """Maps KIS sector codes to Korean sector names"""

    def __init__(self):
        """Initialize with sector code CSV"""
        self.sector_codes = None
        self._load_sector_codes()

    def _load_sector_codes(self):
        """Load sector codes from CSV file"""
        sector_csv = Path(__file__).parent.parent.parent / "sector_codes.csv"

        if not sector_csv.exists():
            logger.warning(f"Sector codes CSV not found: {sector_csv}")
            logger.warning("Run /tmp/download_sector_codes_fixed.py to download sector codes")
            self.sector_codes = pd.DataFrame(columns=['업종코드', '업종명'])
            return

        try:
            self.sector_codes = pd.read_csv(sector_csv)
            logger.debug(f"Loaded {len(self.sector_codes)} sector codes")
        except Exception as e:
            logger.error(f"Failed to load sector codes: {e}")
            self.sector_codes = pd.DataFrame(columns=['업종코드', '업종명'])

    def get_sector_name(self, sector_code: Optional[int]) -> str:
        """
        Get Korean sector name from sector code

        Args:
            sector_code: Integer sector code (e.g., 21 for 금융, 27 for 제조)

        Returns:
            Korean sector name, or "미분류" if not found
        """
        if sector_code is None or pd.isna(sector_code):
            return "미분류"

        # Convert to 4-digit string format (e.g., 21 → "0021")
        code_str = str(int(sector_code)).zfill(4)

        # Look up in sector codes
        matches = self.sector_codes[self.sector_codes['업종코드'] == code_str]

        if len(matches) > 0:
            sector_name = matches.iloc[0]['업종명']
            # Remove leading numbers (e.g., "21금융" → "금융")
            if sector_name and len(sector_name) > 0:
                # Find first non-digit character
                for i, char in enumerate(sector_name):
                    if not char.isdigit():
                        return sector_name[i:]
            return sector_name

        return "미분류"

    def get_sector_info(self, large_code: Optional[int], medium_code: Optional[int],
                       small_code: Optional[int]) -> Dict[str, str]:
        """
        Get comprehensive sector information from codes

        Args:
            large_code: Large category sector code
            medium_code: Medium category sector code
            small_code: Small category sector code

        Returns:
            Dict with 'large', 'medium', 'small' sector names
        """
        return {
            'large': self.get_sector_name(large_code),
            'medium': self.get_sector_name(medium_code),
            'small': self.get_sector_name(small_code)
        }

    def format_sector_display(self, large_code: Optional[int], medium_code: Optional[int]) -> str:
        """
        Format sector for display in AI screening

        Args:
            large_code: Large category sector code
            medium_code: Medium category sector code

        Returns:
            Formatted sector string (e.g., "금융 > 은행")
        """
        large = self.get_sector_name(large_code)
        medium = self.get_sector_name(medium_code)

        if large == "미분류":
            return "미분류"

        if medium == "미분류" or medium == large:
            return large

        return f"{large} > {medium}"
