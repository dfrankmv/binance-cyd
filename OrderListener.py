import json
import time
import helpers
import binance
import websocket

from BinanceAPI import BinanceAPI
from Order import Order
from MQueue import MQueue
from logging import Logger
from keys import API_KEY, SECRET_KEY

class OrderListener:
    binance_client: binance.Client = None
    listen_key: str = None
    mqueue: MQueue = None
    wsa: websocket.WebSocketApp = None
    
    def __init__(self):
        self.mqueue          = MQueue(MQueue.MODE_PUBLISHER)
        self.binance_client  = binance.Client(API_KEY, SECRET_KEY)
        self.listen_key      = self.get_listen_key()
        self.wsa             = self.get_wsa()
        
    def get_listen_key(self):
        try:
            listen_key = self.binance_client.futures_stream_get_listen_key()
            # self.log.info(f"Listen key: {self.listen_key}")
            return listen_key
        except Exception as e:
            # self.log.error(f"Error al obtener la listen key: {e}")
            return ""
        
    def on_message(self, ws: websocket.WebSocket, message: str):
        helpers.run_on_thread(self.handle_message, {"message": message})        

    def handle_message(self, message):
        try:
            message = json.loads(message)
            o = message["o"]
            order = Order(o["s"], o["ps"], o["S"], float(o["q"]), float(o["p"]), float(o["ap"]), o["X"])
            if order.is_filled():
                print(f"Order filled: {o}")
            # if True:
                payload = {}
                payload["order"] = order.to_dict()
                payload["position"] = BinanceAPI.get_position_static(self.binance_client, order.pair, order.direction).to_dict()
                if order.is_increase():
                    payload["type"] = "INCREASE_ORDER_FILLED"
                elif order.is_decrease():
                    payload["type"] = "DECREASE_ORDER_FILLED"
                self.mqueue.send_message(payload)
        except Exception as e:
            # self.log.error(f"Error al procesar el mensaje: {e}")
            pass
    
    def get_wsa(self):
        ws_url = f"wss://fstream.binance.com/ws/{self.listen_key}"
        wsa = websocket.WebSocketApp(ws_url, 
                                    on_message  = self.on_message,
                                    on_open     = lambda ws                 : False, # self.log.info("Conexión WebSocket abierto"),
                                    on_close    = lambda ws, code, message  : False, # self.log.info(f"Conexión WebSocket cerrada. ({code}) {message}"),
                                    on_error    = lambda ws, error          : False # self.log.error(f"Error en el WebSocket: {error}")
                                    )
        return wsa
    
    def keep_alive(self):
        while True:
            try:
                time.sleep(30 * 60)  # 30 mins
                self.binance_client.futures_stream_keepalive(self.listen_key)
                # self.log.info("Listen key renovada.")
            except Exception as e:
                # self.log.error(f"Error al renovar la listen key: {e}")
                break

    def wait_for_exception(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.wsa.close()
            # self.log.info("WebSocket detenido y programa finalizado.")
        except Exception as e:
            # self.log.error(f"Error en el programa principal: {e}")
            self.wsa.close()
            exit(1)

    def keep_listen(self):
        helpers.run_on_thread(self.keep_alive)
        helpers.run_on_thread(self.wsa.run_forever)
        self.wait_for_exception()

if __name__ == "__main__":
    order_listener = OrderListener()
    order_listener.keep_listen()

# OUTPUT
#
# {'e': 'ACCOUNT_UPDATE', 'T': 1719431653964, 'E': 1719431653964, 'a': {'B': [{'a': 'USDT', 'wb': '9.77437417', 'cw': '9.77437417', 'bc': '0'}, {'a': 'BNB', 'wb': '0.00844988', 'cw': '0.00844988', 'bc': '0'}], 'P': [{'s': '1INCHUSDT', 'pa': '-87', 'ep': '0.38466667', 'cr': '1.06110000', 'up': '-0.50381352', 'mt': 'cross', 'iw': '0', 'ps': 'SHORT', 'ma': 'USDT', 'bep': '0.3845974266667'}], 'm': 'ORDER'}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719431653964, 'E': 1719431653964, 'o': {'s': '1INCHUSDT', 'c': '1INCHUSDT_SHORT_2', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '29', 'p': '0.3904', 'ap': '0.3904', 'sp': '0', 'x': 'TRADE', 'X': 'FILLED', 'i': 7968419161, 'l': '29', 'z': '29', 'L': '0.3904', 'n': '0.00000355', 'N': 'BNB', 'T': 1719431653964, 't': 314291713, 'b': '21.9211', 'a': '0', 'm': True, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719431656533, 'E': 1719431656533, 'o': {'s': '1INCHUSDT', 'c': '1INCHUSDT_SHORT_2_20240626195415', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '29', 'p': '0.3865', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 7970588219, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1719431656533, 't': 0, 'b': '33.1296', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719591058613, 'E': 1719591058613, 'o': {'s': 'ARBUSDT', 'c': 'ARBUSDT_SHORT_5_20240627120851', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '13', 'p': '0.808600', 'ap': '0.8086000', 'sp': '0', 'x': 'TRADE', 'X': 'FILLED', 'i': 8343565997, 'l': '13', 'z': '13', 'L': '0.808600', 'n': '0.00000330', 'N': 'BNB', 'T': 1719591058613, 't': 354903023, 'b': '30.2470999', 'a': '10.7237000', 'm': True, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '-0.05514166', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}