import json
import time
import threading
import binance
import websocket

from MQueue import MQueue
from logging import Logger
from keys import API_KEY, SECRET_KEY

def get_listen_key(client: binance.Client):
    try:
        listen_key = client.futures_stream_get_listen_key()
        # self.log.info(f"Listen key: {self.listen_key}")
        return listen_key
    except Exception as e:
        # self.log.error(f"Error al obtener la listen key: {e}")
        return ""

def keep_alive(client: binance.Client, listen_key):
    while True:
        try:
            time.sleep(30 * 60)  # 30 mins
            client.futures_stream_keepalive(listen_key)
            # self.log.info("Listen key renovada.")
        except Exception as e:
            # self.log.error(f"Error al renovar la listen key: {e}")
            break

def get_ws(listen_key, on_message):
    ws_url = f"wss://fstream.binance.com/ws/{listen_key}"
    ws = websocket.WebSocketApp(ws_url, 
                                on_message  = on_message,
                                on_open     = lambda ws                 : False, # self.log.info("Conexión WebSocket abierto"),
                                on_close    = lambda ws, code, message  : False, # self.log.info(f"Conexión WebSocket cerrada. ({code}) {message}"),
                                on_error    = lambda ws, error          : False # self.log.error(f"Error en el WebSocket: {error}")
                                )
    return ws

def message_is_order_filled(message):
    if 'e' in message and message['e'] == 'ORDER_TRADE_UPDATE':
        return message["o"]["X"] == "FILLED"
    else:
        False

def on_message(mqueue: MQueue):
    def _(ws, message):
        try:
            message = json.loads(message)
            if message_is_order_filled(message):
                order = message["o"]
                payload = {
                    "type": "ORDER_FILLED",
                    "order": {
                        "pair": order["s"],
                        "direction": order["ps"],
                        "action": order["S"],
                        "qty": order["q"],
                        "price": order["p"]
                    }
                }
                mqueue.send_message(payload)
        except Exception as e:
            # self.log.error(f"Error al procesar el mensaje: {e}")
            pass
    return _

def wait_for_exception(ws: websocket.WebSocketApp):
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ws.close()
        # self.log.info("WebSocket detenido y programa finalizado.")
    except Exception as e:
        # self.log.error(f"Error en el programa principal: {e}")
        ws.close()
        exit(1)

def run_on_thread(worker, args={}): 
    threading.Thread(target=worker, args=args).start()

if __name__ == "__main__":
    binance_client  = binance.Client(API_KEY, SECRET_KEY)
    listen_key      = get_listen_key(binance_client)
    mqueue          = MQueue(MQueue.MODE_PUBLISHER)
    ws              = get_ws(listen_key, on_message(mqueue))

    run_on_thread(keep_alive, {binance_client, listen_key})
    run_on_thread(ws.run_forever)
    wait_for_exception(ws)

# OUTPUT
#
# {'e': 'ACCOUNT_UPDATE', 'T': 1719431653964, 'E': 1719431653964, 'a': {'B': [{'a': 'USDT', 'wb': '9.77437417', 'cw': '9.77437417', 'bc': '0'}, {'a': 'BNB', 'wb': '0.00844988', 'cw': '0.00844988', 'bc': '0'}], 'P': [{'s': '1INCHUSDT', 'pa': '-87', 'ep': '0.38466667', 'cr': '1.06110000', 'up': '-0.50381352', 'mt': 'cross', 'iw': '0', 'ps': 'SHORT', 'ma': 'USDT', 'bep': '0.3845974266667'}], 'm': 'ORDER'}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719431653964, 'E': 1719431653964, 'o': {'s': '1INCHUSDT', 'c': '1INCHUSDT_SHORT_2', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '29', 'p': '0.3904', 'ap': '0.3904', 'sp': '0', 'x': 'TRADE', 'X': 'FILLED', 'i': 7968419161, 'l': '29', 'z': '29', 'L': '0.3904', 'n': '0.00000355', 'N': 'BNB', 'T': 1719431653964, 't': 314291713, 'b': '21.9211', 'a': '0', 'm': True, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719431656533, 'E': 1719431656533, 'o': {'s': '1INCHUSDT', 'c': '1INCHUSDT_SHORT_2_20240626195415', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '29', 'p': '0.3865', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 7970588219, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1719431656533, 't': 0, 'b': '33.1296', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1719591058613, 'E': 1719591058613, 'o': {'s': 'ARBUSDT', 'c': 'ARBUSDT_SHORT_5_20240627120851', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '13', 'p': '0.808600', 'ap': '0.8086000', 'sp': '0', 'x': 'TRADE', 'X': 'FILLED', 'i': 8343565997, 'l': '13', 'z': '13', 'L': '0.808600', 'n': '0.00000330', 'N': 'BNB', 'T': 1719591058613, 't': 354903023, 'b': '30.2470999', 'a': '10.7237000', 'm': True, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'SHORT', 'cp': False, 'rp': '-0.05514166', 'pP': False, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}