import json
import random
import time

import requests

ORDERS_URL = "http://localhost:5000/orders"

SCENARIOS = [
    ("healthy", {}),
    ("slow", {"slow": "1"}),
    ("inventory_slow", {"inventory_slow": "1"}),
    ("inventory_flake", {"inventory_flake": "1"}),
    ("reserve_fail", {"reserve_fail": "1"}),
    ("bug", {"bug": "1"}),
]


def main() -> None:
    for _ in range(25):
        name, params = random.choice(SCENARIOS)
        item_id = f"sku-{random.randint(100, 999)}"
        try:
            response = requests.post(
                ORDERS_URL,
                params=params,
                data=json.dumps({"item_id": item_id}),
                headers={"Content-Type": "application/json"},
                timeout=3,
            )
            print(name, response.status_code, response.text)
        except requests.RequestException as exc:
            print(name, "error", exc)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
