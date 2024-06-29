import threading
import requests
import json

from keys import FIN_KEY

def run_on_thread(worker, args={}): 
    threading.Thread(target=worker, kwargs=args).start()

def send_finandy_signal(pair: str, direction: str, action: str, qty: float=0):
    headers = {
        'Content-Type': 'application/json',
    }

    url = "https://hook.finandy.com/EUDC58t3FMVzlVtgrlUK"

    payload = {
        "name": "CYD",
        "secret": FIN_KEY,
        "symbol": pair,
        "positionSide": direction.lower(),
        "side": action.lower(),
    }
    if (direction.lower() == "long" and action.lower() == "buy") or (direction.lower() == "short" and action.lower() == "sell"):
        payload["open"] = {
            "amountType": "amount",
            "amount": qty
        }

    payload_json = json.dumps(payload)
    try:
        response = requests.post(url, headers=headers, data=payload_json)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error en la solicitud POST: {e}')
        return None
    
if __name__ == "__main__":
    send_finandy_signal("XRPUSDT", "LONG", "SELL")
