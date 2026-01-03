import datetime as dt
import re
from typing import Any, List, Optional, Tuple

# Date format patterns in order of specificity (most specific first)
# Each tuple contains: (format_string, use_fromisoformat)
# use_fromisoformat=True means we normalize and use fromisoformat (for timezone formats)
DATE_PATTERNS: List[Tuple[str, bool]] = [
    ('%Y:%m:%d %H:%M:%S%z', True),  # 2025:09:24 23:15:15+02:00
    ('%Y:%m:%d %H:%M:%S', False),   # 2020:08:09 19:31:06
    ('%Y:%m:%d', False),             # 2020:08:09
]

# Timezone pattern: +02:00 or -05:00
TIMEZONE_PATTERN = re.compile(r'^([+-])(\d{2}):(\d{2})$')

# Time format patterns in order of specificity (most specific first)
TIME_PATTERNS: List[Tuple[str, bool]] = [
    ('%H:%M:%S%z', True),  # 11:12:41+02:00
    ('%H:%M:%S', False),   # 11:12:41
]


def parse_timezone(value: Any) -> Optional[dt.timezone]:
    """
    Parse a timezone string in format +02:00 or -05:00 to a timezone object.
    
    Args:
        value: The value to parse (must be a string)
    
    Returns:
        A timezone object if the format matches, None otherwise
    
    Example:
        # Parse timezone string
        tz = parse_timezone("+02:00")
        
        # Enhance a naive datetime with timezone info
        naive_dt = dt.datetime(2025, 9, 24, 23, 15, 15)
        aware_dt = naive_dt.replace(tzinfo=tz)
        
        # Or create directly with timezone
        aware_dt = dt.datetime(2025, 9, 24, 23, 15, 15, tzinfo=tz)
    """
    if not isinstance(value, str):
        return None
    
    match = TIMEZONE_PATTERN.match(value.strip())
    if not match:
        return None
    
    sign, hours_str, minutes_str = match.groups()
    hours = int(hours_str)
    minutes = int(minutes_str)
    
    # Calculate total offset in seconds
    offset_seconds = (hours * 3600 + minutes * 60)
    if sign == '-':
        offset_seconds = -offset_seconds
    
    return dt.timezone(dt.timedelta(seconds=offset_seconds))


def parse_time(value: Any, patterns: List[Tuple[str, bool]] = TIME_PATTERNS) -> Optional[dt.time]:
    """
    Parse a time string in format 11:12:41+02:00 or 11:12:41 to a time object.
    
    Args:
        value: The value to parse (must be a string)
        patterns: List of (format_string, use_fromisoformat) tuples to try (defaults to TIME_PATTERNS)
    
    Returns:
        A time object if any pattern matches, None otherwise
    
    Example:
        # Parse time string
        time_obj = parse_time("11:12:41+02:00")
        
        # Merge date from one datetime and time with tz from another datetime
        date_dt = dt.datetime(2025, 9, 24)  # Has date only
        time_dt = dt.datetime(2025, 1, 1, 11, 12, 41, tzinfo=dt.timezone(dt.timedelta(hours=2)))  # Has time+tz
        
        # Method 1: Combine using datetime.combine (preserves timezone from time object)
        combined = dt.datetime.combine(date_dt.date(), time_dt.time())
        
        # Method 2: If you have a parsed time object with timezone
        time_obj = parse_time("11:12:41+02:00")
        if time_obj:
            combined = dt.datetime.combine(date_dt.date(), time_obj)
        
        # Method 3: Manual combination
        combined = dt.datetime(
            date_dt.year, date_dt.month, date_dt.day,
            time_dt.hour, time_dt.minute, time_dt.second,
            time_dt.microsecond, time_dt.tzinfo
        )
    """
    if not isinstance(value, str):
        return None
    
    for format_str, use_fromisoformat in patterns:
        try:
            if use_fromisoformat:
                # For timezone-aware formats, parse as datetime and extract time with tzinfo
                # Create a dummy date to parse the time string
                dummy_datetime_str = f"2000-01-01 {value}"
                parsed_dt = dt.datetime.fromisoformat(dummy_datetime_str)
                # Create time object with tzinfo preserved
                return dt.time(
                    parsed_dt.hour,
                    parsed_dt.minute,
                    parsed_dt.second,
                    parsed_dt.microsecond,
                    parsed_dt.tzinfo
                )
            else:
                return dt.datetime.strptime(value, format_str).time()
        except (ValueError, AttributeError):
            continue
    
    return None


def parse_date(value: Any, patterns: List[Tuple[str, bool]] = DATE_PATTERNS) -> Optional[dt.datetime]:
    """
    Parse a date string using the provided strptime format patterns.
    
    Args:
        value: The value to parse (must be a string)
        patterns: List of (format_string, use_fromisoformat) tuples to try (defaults to DATE_PATTERNS)
    
    Returns:
        A datetime object if any pattern matches, None otherwise
    """
    if not isinstance(value, str):
        return None
    
    for format_str, use_fromisoformat in patterns:
        try:
            if use_fromisoformat:
                # For timezone-aware formats, normalize date part (colons to dashes) and use fromisoformat
                parts = value.split(' ', 1)
                date_part = parts[0].replace(':', '-', 2)
                normalized = f"{date_part} {parts[1]}" if len(parts) > 1 else date_part
                return dt.datetime.fromisoformat(normalized)
            else:
                return dt.datetime.strptime(value, format_str)
        except (ValueError, AttributeError):
            continue
    
    return None

