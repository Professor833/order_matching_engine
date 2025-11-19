import pytest
import asyncio
from ordermatchinengine import Orderbook, LimitOrder, Side


def test_initial_state():
    book = Orderbook()
    # Book should be empty to begin with
    assert len(book) == 0
    assert book.get_bid() is None
    assert book.get_ask() is None


def test_insert():
    book = Orderbook()
    order = LimitOrder(0, Side.BUY, 10, 10)
    book.process_order(order)
    assert len(book) == 1
    assert book.get_bid() == 10
    assert book.get_ask() is None


def test_execution():
    book = Orderbook()
    order = LimitOrder(0, Side.BUY, 10, 10)
    book.process_order(order)
    order = LimitOrder(1, Side.SELL, 10, 10)
    book.process_order(order)

    assert len(book) == 0
    assert book.get_bid() is None
    assert book.get_ask() is None


def test_execution_partial_fill():
    book = Orderbook()
    order = LimitOrder(0, Side.SELL, 5, 105)
    book.process_order(order)
    order = LimitOrder(1, Side.SELL, 5, 106)
    book.process_order(order)
    order = LimitOrder(2, Side.BUY, 1, 105)
    book.process_order(order)
    assert len(book) == 2
    assert book.get_bid() is None
    assert book.get_ask() == 105
    assert len(book.trades) == 1


# Async tests
@pytest.mark.asyncio
async def test_async_initial_state():
    book = Orderbook()
    assert len(book) == 0
    bid = await book.get_bid_async()
    ask = await book.get_ask_async()
    assert bid is None
    assert ask is None


@pytest.mark.asyncio
async def test_async_insert():
    book = Orderbook()
    order = LimitOrder(0, Side.BUY, 10, 10)
    await book.process_order_async(order)
    assert len(book) == 1
    bid = await book.get_bid_async()
    ask = await book.get_ask_async()
    assert bid == 10
    assert ask is None


@pytest.mark.asyncio
async def test_async_execution():
    book = Orderbook()
    order = LimitOrder(0, Side.BUY, 10, 10)
    await book.process_order_async(order)
    order = LimitOrder(1, Side.SELL, 10, 10)
    await book.process_order_async(order)

    assert len(book) == 0
    bid, ask = await book.get_spread_async()
    assert bid is None
    assert ask is None


@pytest.mark.asyncio
async def test_async_concurrent_orders():
    """Test processing multiple orders concurrently."""
    book = Orderbook()

    async def submit_buy_order(order_id: int, price: int):
        order = LimitOrder(order_id, Side.BUY, 10, price)
        await book.process_order_async(order)

    async def submit_sell_order(order_id: int, price: int):
        order = LimitOrder(order_id, Side.SELL, 10, price)
        await book.process_order_async(order)

    # Submit multiple orders concurrently
    await asyncio.gather(
        submit_buy_order(1, 100),
        submit_buy_order(2, 101),
        submit_buy_order(3, 99),
        submit_sell_order(4, 105),
        submit_sell_order(5, 106),
    )

    assert len(book) == 5
    bid = await book.get_bid_async()
    ask = await book.get_ask_async()
    assert bid == 101  # Highest buy price
    assert ask == 105  # Lowest sell price


@pytest.mark.asyncio
async def test_async_get_spread():
    """Test getting bid/ask spread atomically."""
    book = Orderbook()

    await book.process_order_async(LimitOrder(1, Side.BUY, 10, 100))
    await book.process_order_async(LimitOrder(2, Side.SELL, 10, 105))

    bid, ask = await book.get_spread_async()
    assert bid == 100
    assert ask == 105
    assert ask - bid == 5  # Spread is 5


# Legacy test names for backward compatibility
testInitialState = test_initial_state
testInsert = test_insert
testExecution = test_execution
testExecution_marmooli = test_execution_partial_fill
