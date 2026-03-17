from collections import defaultdict
from datetime import datetime


def extract_date(item):
    dt = item.datetime
    return datetime(dt.year, dt.month, dt.day)


def select_best_items_per_day(items):

    items_by_date = defaultdict(list)

    for item in items:
        date = extract_date(item)
        items_by_date[date].append(item)

    selected_items = []

    for date, group in items_by_date.items():

        group_sorted = sorted(
            group,
            key=lambda x: x.properties.get("eo:cloud_cover", 100)
        )

        selected_items.append(group_sorted[0])

    selected_items.sort(key=lambda x: x.datetime)

    print("\n--- STAC ITEM SELECTION ---")
    print(f"Total items: {len(items)}")
    print(f"After dedup: {len(selected_items)}")

    return selected_items