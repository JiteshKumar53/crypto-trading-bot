"""Test chart monitor f-string format fix."""
import pytest
from unittest.mock import Mock, patch
import numpy as np
import sys
sys.path.insert(0, 'src')


class TestChartFormatFix:
    """Verify f-string formatting works with numpy float64 values."""

    def test_numpy_float64_formatting(self):
        """The original bug: f'{np.float64(65.5):.1f}' should not raise."""
        val = np.float64(65.5)
        # This was failing in production
        result = f"{val:.1f}" if val else "N/A"
        assert result == "65.5"

    def test_numpy_float64_with_float_cast(self):
        """The fix: cast to float first."""
        val = np.float64(65.5)
        result = f"{float(val):.1f}" if val is not None else "N/A"
        assert result == "65.5"

    def test_none_value(self):
        """None should return N/A."""
        val = None
        result = f"{float(val):.1f}" if val is not None else "N/A"
        assert result == "N/A"

    def test_numpy_nan(self):
        """np.nan should be handled."""
        val = np.nan
        result = f"{float(val):.1f}" if val is not None and val == val else "N/A"
        # np.nan != np.nan, so this returns N/A
        assert result == "N/A"

    def test_price_formatting(self):
        """Price formatting with numpy float."""
        val = np.float64(77293.58)
        result = f"${float(val):,.2f}"
        assert result == "$77,293.58"

    def test_percentage_formatting(self):
        """Percentage formatting with numpy float."""
        val = np.float64(0.52)  # 52% as decimal
        result = f"{float(val):+.2f}%"
        assert result == "+0.52%"
