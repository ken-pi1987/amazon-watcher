import requests
from bs4 import BeautifulSoup
import config

APPLE_REFURB_URL = "https://www.apple.com/jp/shop/refurbished/mac"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

def fetch_products() -> list[dict]:
    try:
        r = requests.get(APPLE_REFURB_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        products = []
        # 商品リンクを全件取得（h3 > a の構造）
        for a in soup.select("ul.refurbished-category-grid-no-js li a, "
                             "div.refurbished-category-grid li a, "
                             "li.rf-refurb-product a"):
            name = a.get_text(strip=True)
            url = a.get("href", "")
            if not url.startswith("http"):
                url = "https://www.apple.com" + url

            # part numberをURLから抽出（例: /jp/shop/product/FU9D3J/A/...）
            pid = ""
            parts = url.split("/product/")
            if len(parts) > 1:
                pid = parts[1].split("/")[0]

            if name and pid:
                products.append({"name": name, "url": url, "pid": pid})

        return products
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
        pid = p["pid"]
        name = p["name"]

        if not matches_keywords(name):
            continue

        current_ids.add(pid)

        if pid not in prev_ids and prev_ids:
            new_items.append({
                "name": name,
                "price": None,  # HTMLから価格取得は別途対応可
                "url": p["url"],
                "pid": pid,
            })

    return new_items, current_ids
