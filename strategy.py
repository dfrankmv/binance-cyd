import sys
import json
import threading
import time
from Params import Params
import helpers

from MQueue import MQueue
from BinanceAPI import BinanceAPI
from Order import Order
from Position import Position

def run_on_thread(worker, args={}): 
    threading.Thread(target=worker, kwargs=args).start()

class Strategy:
    pair: str = None
    params: Params = None
    mqueue: MQueue = None
    binance_api: BinanceAPI

    def __init__(self, pair: str):
        self.pair        = pair
        self.mqueue      = MQueue(MQueue.MODE_SUBSCRIBER)
        self.binance_api = BinanceAPI(pair)
        self.params      = Params(self.pair)

    def get_local_state(self):
        filename = f"state_{self.pair.lower()}.json"
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return exit(1)
        except json.JSONDecodeError:
            return exit(1)
        
    def save_local_state(self, state: dict):
        filename = f"state_{self.pair.lower()}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(json.dumps(state, indent=4))
        except FileNotFoundError:
            return exit(1)
        except json.JSONDecodeError:
            return exit(1)

    def handle_increase_order_filled(self, message: dict):
        order     = Order.from_dict(message["order"])
        position  = Position.from_dict(message["position"])
        state     = self.get_local_state()
        tp_action = "SELL" if order.is_long() else "BUY"
        if self.pair == order.pair:
            print("SENDING TP ORDER TO BINANCE")
            
            # SEND TP ORDER
            dir_int = 1 if order.direction == "LONG" else -1
            limit_price = self.binance_api.round_to_minprice((1.0 + dir_int * self.params.take_profit_distance_percentage/100.0) * order.xprice)
            self.binance_api.send_order(order.direction, tp_action, limit_price, order.qty) 
            
            # SEND FINANDY SIGNAL
            xdirection = "SHORT" if order.is_long() else "LONG"
            action = "SELL" if order.is_long() else "BUY"
            helpers.send_finandy_signal(order.pair, xdirection, action, state["order_qty_base"][xdirection])
            
            state["breakeven"][order.direction] = position.breakeven
            self.save_local_state(state)
        elif (self.pair != order.pair) and (position.size == 2*order.qty):
            #NOTE A NEW POSITION WAS OPEN ON ORDER.PAIR, RESET TRAILINGS
            this_position = self.binance_api.get_position(order.direction)
            state["breakeven"][order.direction] = this_position.breakeven
            if this_position.size == 0:
                pending_orders = self.binance_api.get_pending_orders(order.direction)
                if len(pending_orders) > 0:
                    # CANCEL ALL PENDING ORDERS (THIS_PAIR, ORDER.DIR) TO FINANDY
                    action = "BUY" if order.is_long() else "SELL"
                    xaction = "SELL" if order.is_long() else "BUY"
                    helpers.send_finandy_signal(self.pair, order.direction, xaction, state["order_qty_base"][order.direction])
            
                    # SEND SIGNAL TO FINANDY
                    helpers.send_finandy_signal(self.pair, order.direction, action, state["order_qty_base"][order.direction])

    def handle_decrease_order_filled(self, message: dict):
        order     = Order.from_dict(message["order"])
        position  = Position.from_dict(message["position"])
        state     = self.get_local_state()
        if self.pair == order.pair and position.size == 0:
            state["breakeven"][order.direction] = None
            state["nof_tps"][order.direction] = 0
            state["order_qty_base"][order.direction] = self.params.base_order_qty
            xdirection = "SHORT" if order.is_long() else "LONG"
            xpending_orders = self.binance_api.get_pending_orders(xdirection)
            if len(xpending_orders) == 0:
                action = "BUY" if order.is_long() else "SELL"
                helpers.send_finandy_signal(self.pair, order.direction, action, state["order_qty_base"][order.direction])
        elif self.pair == order.pair and position.size != 0:
            state["breakeven"][order.direction] = position.breakeven
            state["nof_tps"][order.direction] += 1
            if state["nof_tps"][order.direction] % self.params.take_profits_before_martingale == 0:
                state["order_qty_base"][order.direction] = 2.0 * position.size
        self.save_local_state(state)

    def on_message(self):
        def _(message: dict):
            # print(f"MESSAGE RECEIVED: {message}")
            if message["type"] == "INCREASE_ORDER_FILLED":
                print("MESSAGE RECEIVED!")
                print(message)
                run_on_thread(self.handle_increase_order_filled, {"message": message})
            elif message["type"] == "DECREASE_ORDER_FILLED":
                run_on_thread(self.handle_decrease_order_filled, {"message": message})
        return _

    def listen(self):
        self.mqueue.listen(self.on_message())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python strategy.py <pair>")
        sys.exit(1)
    
    pair = sys.argv[1]
    strategy = Strategy(pair)
    strategy.listen()
