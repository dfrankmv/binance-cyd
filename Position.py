import json

class Position:
    pair: str = None
    direction: str = None
    breakeven: float = None
    size: float = None

    def __init__(self, pair: str, direction: str, breakeven: float, size: float):
        self.pair = pair
        self.direction = direction
        self.breakeven = breakeven
        self.size= size

    def is_long(self): return self.direction == "LONG"
    def is_short(self): return self.direction == "SHORT"

    def to_dict(self):
        return {
            "pair": self.pair,
            "direction": self.direction,
            "breakeven": self.breakeven,
            "size": self.size
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)
    
    @staticmethod
    def from_dict(data):
        return Position(
            pair=data['pair'],
            direction=data['direction'],
            breakeven=data["breakeven"],
            size=data["size"]
        )