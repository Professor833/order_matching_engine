from ordermatchinengine.Order import Side
from time import time


class Trade:
	"""
	Trade
	-----

	A trade object representing an executed match.
	"""
	def __init__(
		self,
		incoming_side: Side,
		price: int | float,
		trade_size: int,
		incoming_order_id: int,
		book_order_id: int
	):
		self.timestamp = int(1e6 * time())
		self.side = incoming_side
		self.price = price
		self.size = trade_size
		self.incoming_order_id = incoming_order_id
		self.book_order_id = book_order_id

	def __repr__(self) -> str:
		return f"Executed: {self.side} {self.size} units at {self.price}"
