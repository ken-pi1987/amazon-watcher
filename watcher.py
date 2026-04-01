import time
import json
import os
from datetime import datetime
from checkers import amazon, apple
import notifier
import config

STATE_FILE = os.path.expanduser("~/amazon-watcher/state.json")

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def format_notify(source_label: str, items: list[dict]) -> str:
    lines = [f"\n🆕 【新着入荷：{source_label}】"]
    for item in items:
        price_text = f"¥{item['price']}" if item.get("price") else "価格不明"
        lines.append(f"\n📦 {item['name']}\n💰 {price_text}\n🔗 {item['url']}")
    return "\n".join(lines)

def main():
    print("[起動] 整備済み品ウォッチャー（Apple公式 + Amazon）")
    notifier.send(
        "✅ ウォッチャー起動\n"
        f"・Apple公式：{len(config.APPLE_KEYWORDS)}キーワード監視\n"
        f"・Amazon：ASIN {len(config.AMAZON_KNOWN_ASINS)}件 + "
        f"検索 {len(config.AMAZON_SEARCH_URLS)}件"
    )

    state = load_state()
    apple_ids: set = set(state.get("apple_ids", []))
    amazon_prev_asins: dict = state.get("amazon_search_asins", {})
    amazon_asin_stock: dict = state.get("amazon_asin_stock", {})

    tick = 0
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] チェック #{tick}")

        if tick % (config.INTERVAL_APPLE // config.INTERVAL_AMAZON) == 0:
            print("  [Apple公式] チェック中...")
            new_apple, apple_ids = apple.check(apple_ids)
            if new_apple:
                notifier.send(format_notify("Apple公式認定整備済み品", new_apple))
            else:
                print(f"  [Apple公式] 新着なし（監視中: {len(apple_ids)}件）")

        for target in config.AMAZON_KNOWN_ASINS:
            asin = amazon._extract_asin(target["url"])
            result = amazon.check_asin(target)
            if result:
                was = amazon_asin_stock.get(asin, False)
                is_now = result["in_stock"]
                print(f"  [Amazon ASIN] {target['name']}: "
                      f"{'✅在庫あり' if is_now else '❌在庫なし'}")
                if is_now and not was:
                    notifier.send(format_notify("Amazon整備済み品（入荷）", [result]))
                amazon_asin_stock[asin] = is_now

        for target in config.AMAZON_SEARCH_URLS:
            key = target["name"]
            prev = set(amazon_prev_asins.get(key, []))
            new_items, current = amazon.check_search(target, prev)
            print(f"  [Amazon検索] {key}: "
                  f"新着 {len(new_items)}件 / 現在 {len(current)}件")
            if new_items:
                notifier.send(format_notify("Amazon検索：新規出品", new_items))
            amazon_prev_asins[key] = list(current)

        save_state({
            "apple_ids": list(apple_ids),
            "amazon_search_asins": amazon_prev_asins,
            "amazon_asin_stock": amazon_asin_stock,
        })

        tick += 1
        time.sleep(config.INTERVAL_AMAZON)

if __name__ == "__main__":
    main()
