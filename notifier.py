import requests
import config

def send(message: str):
    try:
        r = requests.post(
            config.DISCORD_WEBHOOK_URL,
            json={"content": message},
            timeout=10
        )
        r.raise_for_status()
        print(f"[Discord通知] {message[:60]}...")
    except Exception as e:
        print(f"[Discord通知エラー] {e}")
