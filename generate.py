
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import holidays
from dateutil.easter import easter
from icalendar import Calendar, Event

CURRENT_YEAR = date.today().year
YEARS = range(CURRENT_YEAR - 1, CURRENT_YEAR + 8)

# Federal holidays, including observed dates
federal = holidays.US(years=YEARS, observed=True)

# Collect events by date so overlapping holidays are merged.
events = {}

def add(day, name, category):
    if day not in events:
        events[day] = {"names": set(), "categories": set()}

    events[day]["names"].add(name)
    events[day]["categories"].add(category)


# Federal holidays
for day, name in federal.items():
    add(day, str(name), "Federal holiday")


# Date calculation helpers
def nth_weekday(year, month, weekday, n):
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year, month, weekday):
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)

    return last - timedelta(days=(last.weekday() - weekday) % 7)


# New Jersey-specific holidays
for year in YEARS:
    easter_sunday = easter(year)

    # Good Friday
    add(
        easter_sunday - timedelta(days=2),
        "Good Friday",
        "New Jersey state holiday"
    )

    # NJ Election Day: first Tuesday after the first Monday
    first_monday = nth_weekday(year, 11, 0, 1)
    election_day = first_monday + timedelta(days=1)

    add(
        election_day,
        "New Jersey Election Day",
        "New Jersey state holiday"
    )


# Major cultural and family observances
for year in YEARS:
    easter_sunday = easter(year)

    observances = {
        date(year, 2, 14): "Valentine's Day",
        date(year, 3, 17): "St. Patrick's Day",
        easter_sunday: "Easter Sunday",
        date(year, 4, 22): "Earth Day",
        nth_weekday(year, 5, 6, 2): "Mother's Day",
        nth_weekday(year, 6, 6, 3): "Father's Day",
        nth_weekday(year, 7, 6, 4): "Parents' Day",
        date(year, 10, 31): "Halloween",
        date(year, 12, 24): "Christmas Eve",
        date(year, 12, 31): "New Year's Eve",
    }

    # Grandparents' Day: first Sunday after Labor Day
    labor_day = nth_weekday(year, 9, 0, 1)
    observances[labor_day + timedelta(days=6)] = "Grandparents' Day"

    for day, name in observances.items():
        add(day, name, "Observance")


# Create ICS calendar
cal = Calendar()
cal.add("prodid", "-//US and NJ Combined Holidays//EN")
cal.add("version", "2.0")
cal.add("X-WR-CALNAME", "US and New Jersey Holidays")
cal.add(
    "X-WR-CALDESC",
    "US federal holidays, New Jersey holidays, "
    "and major family observances"
)
cal.add("X-WR-CALSCALE", "GREGORIAN")

for day, data in sorted(events.items()):
    event = Event()

    event.add("uid", f"{day.isoformat()}@nj-holidays")
    event.add("dtstamp", datetime.now(timezone.utc))
    event.add("dtstart", day)
    event.add("dtend", day + timedelta(days=1))

    event.add("summary", " / ".join(sorted(data["names"])))
    event.add("description", "Categories: " +
              ", ".join(sorted(data["categories"])))
    event.add("categories", sorted(data["categories"]))

    cal.add_component(event)


# Publishable output
output = Path("site")
output.mkdir(exist_ok=True)

(output / "holidays.ics").write_bytes(cal.to_ical())

print(f"Generated {len(events)} unique calendar dates")
print(f"Calendar covers {min(YEARS)} through {max(YEARS)}")
