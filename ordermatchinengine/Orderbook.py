from ordermatchinengine.Order import *
from ordermatchinengine.Trade import *
from sortedcontainers import SortedList
import asyncio
from typing import Optional


class Orderbook:
	"""
	An orderbook.
	-------------

	It can store and process orders.
	Supports both synchronous and asynchronous order processing.
	"""
	def __init__(self):
		self.bids: SortedList[LimitOrder] = SortedList()
		self.asks: SortedList[LimitOrder] = SortedList()
		self.trades: list[Trade] = []
		self._lock = asyncio.Lock()

	async def process_order_async(self, incoming_order: Order) -> None:
		"""
		Asynchronously processes an order with lock protection.

		Use this method when processing orders from multiple coroutines.
		"""
		async with self._lock:
			self._process_order_internal(incoming_order)

	def process_order(self, incoming_order: Order) -> None:
		"""
		Synchronously processes an order.

		Depending on the type of order the following can happen:
		- Market Order
		- Limit Order
		- Cancel Order
		"""
		self._process_order_internal(incoming_order)

	def _process_order_internal(self, incoming_order: Order) -> None:
		"""
		Internal order processing logic.
		"""
		if incoming_order.__class__ == CancelOrder:
			for order in self.bids:
				if incoming_order.order_id == order.order_id:
					self.bids.discard(order)
					break

			for order in self.asks:
				if incoming_order.order_id == order.order_id:
					self.asks.discard(order)
					break

			return  # Exiting process order

		def while_clause() -> bool:
			"""
			Determines whether to continue the while-loop
			"""
			if incoming_order.side == Side.BUY:
				if incoming_order.__class__ == LimitOrder:
					return len(self.asks) > 0 and incoming_order.price >= self.asks[0].price
				elif incoming_order.__class__ == MarketOrder:
					return len(self.asks) > 0
			else:
				if incoming_order.__class__ == LimitOrder:
					return len(self.bids) > 0 and incoming_order.price <= self.bids[0].price
				elif incoming_order.__class__ == MarketOrder:
					return len(self.bids) > 0
			return False

		# while there are orders and the orders requirements are matched
		while while_clause():
			book_order: LimitOrder | None = None
			if incoming_order.side == Side.BUY:
				book_order = self.asks.pop(0)
			else:
				book_order = self.bids.pop(0)

			if incoming_order.remaining == book_order.remaining:  # if the same volume
				volume = incoming_order.remaining
				incoming_order.remaining -= volume
				book_order.remaining -= volume
				self.trades.append(Trade(
					incoming_order.side, book_order.price, volume, incoming_order.order_id, book_order.order_id))
				break

			elif incoming_order.remaining > book_order.remaining:  # incoming has greater volume
				volume = book_order.remaining
				incoming_order.remaining -= volume
				book_order.remaining -= volume
				self.trades.append(Trade(
					incoming_order.side, book_order.price, volume, incoming_order.order_id, book_order.order_id))

			elif incoming_order.remaining < book_order.remaining:  # book has greater volume
				volume = incoming_order.remaining
				incoming_order.remaining -= volume
				book_order.remaining -= volume
				self.trades.append(Trade(
					incoming_order.side, book_order.price, volume, incoming_order.order_id, book_order.order_id))

				if book_order.side == Side.SELL:
					self.asks.add(book_order)
				else:
					self.bids.add(book_order)
				break

		if incoming_order.remaining > 0 and incoming_order.__class__ == LimitOrder:
			if incoming_order.side == Side.BUY:
				self.bids.add(incoming_order)
			else:
				self.asks.add(incoming_order)

	def get_bid(self) -> Optional[int]:
		return self.bids[0].price if len(self.bids) > 0 else None

	def get_ask(self) -> Optional[int]:
		return self.asks[0].price if len(self.asks) > 0 else None

	async def get_bid_async(self) -> Optional[int]:
		"""Async version of get_bid with lock protection."""
		async with self._lock:
			return self.bids[0].price if len(self.bids) > 0 else None

	async def get_ask_async(self) -> Optional[int]:
		"""Async version of get_ask with lock protection."""
		async with self._lock:
			return self.asks[0].price if len(self.asks) > 0 else None

	async def get_spread_async(self) -> tuple[Optional[int], Optional[int]]:
		"""Get both bid and ask prices atomically."""
		async with self._lock:
			bid = self.bids[0].price if len(self.bids) > 0 else None
			ask = self.asks[0].price if len(self.asks) > 0 else None
			return (bid, ask)

	def __repr__(self) -> str:
		lines: list[str] = []
		lines.append("-" * 5 + "OrderBook" + "-" * 5)

		lines.append("\nAsks:")
		asks = self.asks.copy()
		while len(asks) > 0:
			lines.append(str(asks.pop()))

		lines.append("\t" * 3 + "Bids:")
		bids = list(reversed(self.asks.copy()))
		while len(bids) > 0:
			lines.append("\t" * 3 + str(bids.pop()))

		lines.append("-" * 20)
		return "\n".join(lines)

	def __len__(self) -> int:
		return len(self.asks) + len(self.bids)
