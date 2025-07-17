import time

import requests

TIKTOK_ACCESS_TOKEN = "da24809f46c8b58abd71ebcc60da5096e180bd91"
PIXEL_CODE = "D1SBUPRC77U25MKH1E40"


def send_tiktok_event(phone_number, value_bhd):
    url = "https://business-api.tiktok.com/open_api/v1.3/event/track/"

    headers = {
        "Content-Type": "application/json",
        "Access-Token": TIKTOK_ACCESS_TOKEN
    }
    payload = {
        "event_source": "web",
        "event_source_id": PIXEL_CODE,
        "data": [
            {
                "event": "PlaceAnOrder",
                "event_time": int(time.time()),
                "user": {
                    "phone": f"+{phone_number}"
                },
                "properties": {
                    "currency": "BHD",
                    "content_type": "product",
                    "value": value_bhd
                }
            }
        ]
    }

    response = requests.post(url, json=payload, headers=headers)
    print("TikTok response:", response.status_code, response.text)
    return response.ok