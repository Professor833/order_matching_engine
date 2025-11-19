from ordermatchinengine import Order, CancelOrder, MarketOrder, LimitOrder, Side


def test_order_initial_state():
    order = Order(1)
    assert isinstance(order.order_id, int)
    assert isinstance(order.time, int)
    assert order.order_id == 1


def test_cancel_order_initial_state():
    order = CancelOrder(1)
    assert isinstance(order.order_id, int)
    assert isinstance(order.time, int)
    assert order.order_id == 1


def test_market_order_initial_state():
    order = MarketOrder(1, Side.BUY, 10)
    assert isinstance(order.order_id, int)
    assert isinstance(order.time, int)
    assert order.order_id == 1
    assert order.side == Side.BUY
    assert order.size == 10
    assert order.remaining == 10


def test_limit_order_initial_state():
    order = LimitOrder(1, Side.BUY, 10, 100)
    assert isinstance(order.order_id, int)
    assert isinstance(order.time, int)
    assert order.order_id == 1
    assert order.side == Side.BUY
    assert order.size == 10
    assert order.price == 100
    assert order.remaining == 10


def test_limit_order_comparison_price():
    """Test that limit orders sort by price correctly."""
    buy1 = LimitOrder(1, Side.BUY, 10, 100)
    buy2 = LimitOrder(2, Side.BUY, 10, 101)
    # For BUY orders, higher price should come first
    assert buy2 < buy1  # 101 has higher priority than 100

    sell1 = LimitOrder(3, Side.SELL, 10, 100)
    sell2 = LimitOrder(4, Side.SELL, 10, 101)
    # For SELL orders, lower price should come first
    assert sell1 < sell2  # 100 has higher priority than 101


def test_limit_order_repr():
    """Test string representation of limit orders."""
    order = LimitOrder(1, Side.BUY, 10, 100)
    repr_str = repr(order)
    assert "BUY" in repr_str
    assert "10" in repr_str
    assert "100" in repr_str


def test_market_order_repr():
    """Test string representation of market orders."""
    order = MarketOrder(1, Side.SELL, 50)
    repr_str = repr(order)
    assert "SELL" in repr_str
    assert "50" in repr_str


def test_cancel_order_repr():
    """Test string representation of cancel orders."""
    order = CancelOrder(42)
    repr_str = repr(order)
    assert "42" in repr_str


# Legacy test name for backward compatibility
test_initialStates = test_order_initial_state
