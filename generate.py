
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import holidays
from dateutil.easter import easter
from icalendar import Calendar, Event

CURRENT_YEAR = date.today().year
YEARS = range(CURRENT_YEAR - 1, CURRENT_YEAR + 8)

events = {}


def add(day, name, category):
    if day not in events:
        events[day] = {
            "names": set(),
            "categories": set(),
        }

    events[day]["names"].add(name)
    events[day]["categories"].add(category)


def nth_weekday(year, month, weekday, occurrence):
    first_day = date(year, month, 1)
    offset = (weekday - first_day.weekday()) % 7
    return first_day + timedelta(days=offset + (occurrence - 1) * 7)


# US federal holidays, including observed dates
federal_holidays = holidays.US(years=YEARS, observed=True)

for day, name in federal_holidays.items():
    add(day, name, "US Federal Holiday")


# New Jersey state holidays
for year in YEARS:
    easter_sunday = easter(year)

    # Good Friday
    add(
        easter_sunday - timedelta(days=2),
        "Good Friday",
        "New Jersey State Holiday",
    )

    # New Jersey Election Day: first Tuesday after the first Monday in November
    november_first = date(year, 11, 1)
    first_monday = november_first + timedelta(
        days=(0 - november_first.weekday()) % 7
    )
    election_day = first_monday + timedelta(days=1)

    add(
        election_day,
        "Election Day",
        "New Jersey State Holiday",
    )


# Major family and cultural observances
for year in YEARS:
    add(date(year, 2, 14), "Valentine's Day", "Observance")
    add(date(year, 3, 17), "St. Patrick's Day", "Observance")
    add(easter(year), "Easter Sunday", "Observance")
    add(date(year, 4, 22), "Earth Day", "Observance")

    add(
        nth_weekday(year, 5, 6, 2),
        "Mother's Day",
        "Family Observance",
    )

    add(
        nth_weekday(year, 6, 6, 3),
        "Father's Day",
        "Family Observance",
    )

    add(
        nth_weekday(year, 7, 6, 4),
        "Parents' Day",
        "Family Observance",
    )

    add(date(year, 10, 31), "Halloween", "Observance")

    # Grandparents' Day: Sunday after Labor Day
    labor_day = nth_weekday(year, 9, 0, 1)
    grandparents_day = labor_day + timedelta(days=6)

    add(
        grandparents_day,
        "Grandparents' Day",
        "Family Observance",
    )


# Build calendar
cal = Calendar()
cal.add("prodid", "-//US and New Jersey Holiday Calendar//EN")
cal.add("version", "2.0")
cal.add("calscale", "GREGORIAN")
cal.add("X-WR-CALNAME", "US and New Jersey Holidays")
cal.add(
    "X-WR-CALDESC",
    "Combined US federal, New Jersey state, and major family observances.",
)

for day in sorted(events):
    details = events[day]

    event = Event()
    event.add("uid", f"{day.isoformat()}@nj-holidays")
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("dtstart", day)
    event.add("dtend", day + timedelta(days=1))

    names = sorted(details["names"])
    categories = sorted(details["categories"])

    event.add("summary", " / ".join(names))
    event.add("description", ", ".join(categories))
    event.add("categories", categories)

    cal.add_component(event)


# Write calendar and website
output = Path("site")
output.mkdir(parents=True, exist_ok=True)

(output / "holidays.ics").write_bytes(cal.to_ical())

(output / "index.html").write_text(
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>US and New Jersey Holidays</title>
</head>
<body>
<h1>US and New Jersey Holidays</h1>
<p>Subscribe to the combined federal, New Jersey,
and family holiday calendar.</p>
<p><a href="holidays.ics">Download or subscribe to the ICS calendar</a></p>
</body>
</html>
""",
    encoding="utf-8",
)
