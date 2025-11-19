from enum import Enum
from time import time
from typing import Self


class Side(Enum):
    BUY = 0
    SELL = 1


class Order:
    def __init__(self, order_id: int):
        self.order_id = order_id
        self.time = int(1e6 * time())

    def __getType__(self) -> type[Self]:
        return self.__class__


class CancelOrder(Order):
    def __init__(self, order_id: int):
        super().__init__(order_id)

    def __repr__(self) -> str:
        return f"Cancel Order: {self.order_id}."


class MarketOrder(Order):
    def __init__(self, order_id: int, side: Side, size: int):
        super().__init__(order_id)
        self.side = side
        self.size = self.remaining = size

    def __repr__(self) -> str:
        side_str = "BUY" if self.side == Side.BUY else "SELL"
        return f"Market Order: {side_str} {self.remaining} units."


class LimitOrder(MarketOrder):
    def __init__(self, order_id: int, side: Side, size: int, price: int | float):
        super().__init__(order_id, side, size)
        self.price = price

    def __lt__(self, other: Self) -> bool:
        if self.price != other.price:
            if self.side == Side.BUY:
                return self.price > other.price
            else:
                return self.price < other.price

        elif self.time != other.time:
            return self.time < other.time

        elif self.size != other.size:
            return self.size < other.size

        return False

    def __repr__(self) -> str:
        side_str = "BUY" if self.side == Side.BUY else "SELL"
        return f"Limit Order: {side_str} {self.remaining} units at {self.price}."
