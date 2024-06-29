from Params import Params
from Position import Position
from keys import API_KEY, SECRET_KEY
from binance import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException


class BinanceAPI:
    pair: str = None
    client: Client = None
    price_decimals: int = None 
    qty_decimals: int = None

    def __init__(self, pair: str):
        params              = Params(pair)
        self.pair           = pair
        self.client         = Client(API_KEY, SECRET_KEY)
        self.qty_decimals   = params.qty_decimals
        self.price_decimals = params.price_decimals

    def round_to_minprice(self, price): return round(price, self.price_decimals)
    def round_to_minqty(self, qty): round(qty, self.qty_decimals) if round(qty, self.qty_decimals) * (10 ** self.qty_decimals) % 2 == 0 else (round(qty, self.qty_decimals) + 10**-self.qty_decimals)

    def get_position(self, direction: str):
        return BinanceAPI.get_position_static(self.client, self.pair, direction)
    
    @staticmethod
    def get_position_static(client: Client, pair: str, direction: str):
        pair_positions = client.futures_position_information(symbol=pair)
        for pos in pair_positions:
            if direction == pos["positionSide"]:
                return Position(pos["symbol"], pos["positionSide"], float(pos["breakEvenPrice"]), float(pos["positionAmt"]))
        return None
    
    def send_order(self, direction:str, action:str, limit_price: float, qty: float):
        try:
            self.client.futures_create_order(
                symbol       = self.pair,
                side         = action,
                type         = ORDER_TYPE_LIMIT,
                timeInForce  = TIME_IN_FORCE_GTC,
                quantity     = qty,
                price        = limit_price,
                positionSide = direction 
            )
        except BinanceAPIException as e:
            print(f"Binance API error: {e}")
        except BinanceOrderException as e:
            print(f"Order error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def cancel_increase_orders_by_direction(self, direction:str):
        orders = self.client.futures_get_open_orders(symbol=self.pair)
        for order in orders:
            if direction == 'LONG' and order['side'] == 'BUY':
                result = self.client.futures_cancel_order(symbol=self.pair, orderId=order['orderId'])
                print(result)
            elif direction == 'SHORT' and order['side'] == 'SELL':
                result = self.client.futures_cancel_order(symbol=self.pair, orderId=order['orderId'])
                print(result)

    def get_pending_orders(self, direction:str):
        open_orders = self.client.futures_get_open_orders(symbol=self.pair)
        if direction == "LONG":
            limit_orders = [order for order in open_orders if order['side'] == 'BUY' and order['type'] == 'LIMIT']
        elif direction == "SHORT":
            limit_orders = [order for order in open_orders if order['side'] == 'SELL' and order['type'] == 'LIMIT']
        return limit_orders