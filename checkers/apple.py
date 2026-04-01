import requests
import config

APPLE_REFURB_URL = (
    "https://www.apple.com/jp/shop/product-finderbag"
    "?filters=restocked&type=REFURBISHED_MACS"
    "&sort=NEWEST&perPage=20&pl=true"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.apple.com/jp/shop/refurbished/mac",
}

def fetch_products() -> list[dict]:
    try:
        r = requests.get(APPLE_REFURB_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("products", [])
    except Exception as e:
        print(f"[Apple取得エラー] {e}")
        return []

def matches_keywords(product_name: str) -> bool:
    name_lower = product_name.lower()
    return all(kw.lower() in name_lower for kw in config.APPLE_KEYWORDS)

def check(prev_ids: set) -> tuple[list[dict], set]:
    products = fetch_products()
    current_ids = set()
    new_items = []

    for p in products:
        pid = p.get("partNumber", "")
        name = p.get("name", "")
        price = p.get("price", {}).get("currentPrice", {}).get("raw_amount", "")
        url = "https://www.apple.com/jp/shop/product/" + pid

        if not matches_keywords(name):
            continue

        current_ids.add(pid)

        if pid not in prev_ids and prev_ids:
            new_items.append({
                "name": name,
                "price": price,
                "url": url,
                "pid": pid,
            })

    return new_items, current_ids
