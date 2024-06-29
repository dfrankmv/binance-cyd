import os
import json

class Params:
    base_order_qty: float                  = None
    take_profit_distance_percentage: float = None
    win_distance_percentage: float         = None
    martingale_factor: float               = None
    take_profits_before_martingale: int    = None
    trailing_distance: float               = None
    qty_decimals: int                      = None 
    price_decimals: int                    = None

    def __init__(self, pair: str) -> None:
        script_dir_path = os.path.dirname(os.path.abspath(__file__))
        params_file_path = os.path.join(script_dir_path, 'params.json')
        params = json.load(open(params_file_path, "r")).get(pair, {   # DEFAULT PARAMS
            "base_order_qty"                  : 0.0,
            "take_profit_distance_percentage" : 1.0,
            "win_distance_percentage"         : 5.0,
            "martingale_factor"               : 2.0,
            "take_profits_before_martingale"  : 5,
            "trailing_distance"               : 2.0
        })
        decimals_file_path = os.path.join(script_dir_path, 'decimals.json')
        decimals = json.load(open(decimals_file_path, "r")).get(pair)
        self.base_order_qty                  = params["base_order_qty"]
        self.take_profit_distance_percentage = params["take_profit_distance_percentage"]
        self.win_distance_percentage         = params["win_distance_percentage"]
        self.martingale_factor               = params["martingale_factor"]
        self.take_profits_before_martingale  = params["take_profits_before_martingale"]
        self.trailing_distance               = params["trailing_distance"]
        self.qty_decimals                    = decimals["qty_decs"]
        self.price_decimals                  = decimals["price_decs"]

# DEMO
if __name__ == "__main__":
    print(Params("BTCUSDT").base_order_amount)
    print(Params("BTCUSDT").price_decimals)