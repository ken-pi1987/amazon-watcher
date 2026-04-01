import requests
from bs4 import BeautifulSoup
import config

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}

def _extract_asin(url: str) -> str:
    if "/dp/" in url:
        return url.split("/dp/")[-1].split("/")[0].split("?")[0]
    return url

def check_asin(target: dict) -> dict | None:
    try:
        r = requests.get(target["url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        add_to_cart = soup.find("input", {"id": "add-to-cart-button"})
        unavailable = soup.find(string=lambda t: t and "現在在庫切れ" in t)
        in_stock = bool(add_to_cart) and not unavailable
        price_elem = soup.find("span", {"class": "a-price-whole"})
        price = price_elem.get_text(strip=True) if price_elem else None
        return {
            "name": target["name"],
            "url": target["url"],
            "in_stock": in_stock,
            "price": price,
            "source": "amazon_asin",
        }
    except Exception as e:
        print(f"[Amazon ASINエラー] {e}")
        return None

def check_search(target: dict, prev_asins: set) -> tuple[list[dict], set]:
    try:
        r = requests.get(target["url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select('[data-asin]')
        current_asins = set()
        new_items = []

        for item in items:
            asin = item.get("data-asin", "")
            if not asin:
                continue
            current_asins.add(asin)

            name_elem = (item.select_one("h2 a span") or
                         item.select_one(".a-size-medium") or
                         item.select_one(".a-size-base-plus"))
            name = name_elem.get_text(strip=True) if name_elem else asin

            price_elem = item.select_one(".a-price .a-offscreen")
            price = price_elem.get_text(strip=True) if price_elem else None

            link_elem = item.select_one("h2 a")
            url = ("https://www.amazon.co.jp" + link_elem["href"]
                   if link_elem else "")

            if asin not in prev_asins and prev_asins:
                new_items.append({
                    "name": name,
                    "url": url,
                    "price": price,
                    "source": "amazon_search",
                })

        return new_items, current_asins
    except Exception as e:
        print(f"[Amazon 検索エラー] {e}")
        return [], prev_asins
