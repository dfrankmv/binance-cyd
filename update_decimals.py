import requests
import json
import os

def num_decs(number_str):
    from decimal import Decimal
    number = Decimal(number_str)
    normalized_number = number.normalize()
    normalized_str = str(normalized_number)
    if '.' in normalized_str:
        return len(normalized_str.split('.')[1])
    else:
        return 0

jsonres = requests.request(url="https://fapi.binance.com/fapi/v1/exchangeInfo", method="GET").json()

items = jsonres["symbols"]
res = {}
for item in items:
    symbol = item["symbol"]
    filters = item["filters"]
    price_decs = ""
    qty_decs = ""
    for filter in filters:
        if filter["filterType"] == "PRICE_FILTER":
            price_decs = num_decs(filter["tickSize"])
        if filter["filterType"] == "LOT_SIZE":
            qty_decs = num_decs(filter["stepSize"])
    res[symbol] = {"price_decs": price_decs, "qty_decs": qty_decs}

script_directory = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_directory, 'decimals.json')
json.dump(res, open(json_file_path, "w"), indent=4)
