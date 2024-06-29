import json

class Order:
    pair: str = None
    direction: str = None
    action: str = None 
    qty: float = None
    price: float = None
    xprice: float = None
    xstatus: str = None

    def __init__(self, pair: str, direction: str, action: str, qty: float, price: float, xprice: float, xstatus: str):
        self.pair = pair
        self.direction = direction
        self.action = action
        self.qty = qty
        self.price = price
        self.xprice = xprice
        self.xstatus = xstatus

    def is_long(self): return self.direction == "LONG"
    def is_short(self): return self.direction == "SHORT"
    def is_filled(self): return self.xstatus == "FILLED"

    def is_increase(self):
        long_cond  = self.direction == "LONG" and self.action == "BUY"
        short_cond = self.direction == "SHORT" and self.action == "SELL"
        return long_cond or short_cond

    def is_decrease(self):
        long_cond  = self.direction == "LONG" and self.action == "SELL"
        short_cond = self.direction == "SHORT" and self.action == "BUY"
        return long_cond or short_cond

    def to_dict(self):
        return {
            "pair": self.pair,
            "direction": self.direction,
            "action": self.action,
            "qty": self.qty,
            "price": self.price,
            "xprice": self.xprice,
            "xstatus": self.xstatus
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
    
    @staticmethod
    def from_dict(data):
        return Order(
            pair=data['pair'],
            direction=data['direction'],
            action=data['action'],
            qty=data['qty'],
            price=data['price'],
            xprice=data['xprice'],
            xstatus=data['xstatus']
        )
