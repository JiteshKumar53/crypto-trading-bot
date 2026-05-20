"""Chart monitor f-string safety check — prevents format specifier bugs."""

def safe_rsi_str(rsi_value) -> str:
    """Safely format RSI value, handling numpy types and None."""
    if rsi_value is None:
        return "N/A"
    try:
        # Handle numpy types by converting to Python float first
        val = float(rsi_value)
        if val != val:  # Check for NaN
            return "N/A"
        return f"{val:.1f}"
    except (ValueError, TypeError):
        return str(rsi_value)


def safe_pct_str(value) -> str:
    """Safely format percentage value."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
        if val != val:  # NaN check
            return "N/A"
        return f"{val:.2f}"
    except (ValueError, TypeError):
        return str(value)


def safe_price_str(value) -> str:
    """Safely format price value with commas."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
        if val != val:  # NaN check
            return "N/A"
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def safe_volume_str(value) -> str:
    """Safely format volume multiplier."""
    if value is None:
        return "N/A"
    try:
        val = float(value)
        if val != val:
            return "N/A"
        return f"{val:.1f}x"
    except (ValueError, TypeError):
        return str(value)
