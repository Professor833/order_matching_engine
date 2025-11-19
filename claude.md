# Order Matching Engine - Codebase Documentation

## Project Overview

This is a high-performance order matching engine implemented in Python, designed to process buy and sell orders using a price-time priority algorithm. The engine achieves throughput of 400,000+ orders per second on a single thread and 850,000+ orders per second when running multiple orderbooks in parallel.

**Author:** Lalit Vavdara
**License:** MIT
**Language:** Python 3.11+
**Status:** Work in Progress

## Key Features

- **Async/Await Support:** Full asynchronous order processing with `asyncio`
- **Lock Protection:** Thread-safe async operations with `asyncio.Lock`
- **Python 3.11+ Type Hints:** Modern type annotations including `Self`, union types (`|`), and generic types
- **Backward Compatibility:** Synchronous API still available alongside async methods

## Architecture

### System Design

The order matching engine implements a **price-time priority** matching algorithm, the standard used by most stock exchanges:

1. **Price Priority:** Orders with better prices execute first (higher for buys, lower for sells)
2. **Time Priority:** At the same price level, earlier orders execute first (FIFO)
3. **Size Priority:** As a tertiary tiebreaker, smaller orders execute first

### Core Components

```
ordermatchinengine/
├── Order.py          # Order types and trading side definitions
├── Orderbook.py      # Core matching engine logic
└── Trade.py          # Trade execution records
```

## File Structure

```
order-matching-engine/
├── ordermatchinengine/          # Main package
│   ├── __init__.py
│   ├── Order.py                 # Order class hierarchy
│   ├── Orderbook.py             # Matching engine
│   └── Trade.py                 # Trade records
├── tests/
│   ├── unit/
│   │   ├── test_order.py        # Order unit tests
│   │   └── test_orderbook.py    # Orderbook unit tests
│   └── performance/
│       └── Benchmark.py         # Performance benchmarks
├── .gitignore
├── LICENSE                      # MIT License
├── README.md
└── requirements.txt             # Python dependencies
```

## Core Classes and Components

### 1. Order Types ([Order.py](ordermatchinengine/Order.py))

#### Side Enumeration
```python
class Side(Enum):
    BUY = 0
    SELL = 1
```

#### Order Class Hierarchy

**Base Order Class:**
- **Attributes:**
  - `order_id`: Unique identifier for the order
  - `time`: Microsecond precision timestamp (`int(1e6 * time())`)
- **Methods:**
  - `__getType__()`: Returns the order's class type

**CancelOrder (inherits Order):**
- Used to cancel existing orders in the book
- Only requires `order_id` to identify which order to cancel

**MarketOrder (inherits Order):**
- Executes immediately at best available price
- **Attributes:**
  - `side`: BUY or SELL
  - `size`: Order quantity
  - `remaining`: Unfilled quantity (updated during matching)
- No price limit - takes whatever is available

**LimitOrder (inherits MarketOrder):**
- Executes only at specified price or better
- **Additional Attributes:**
  - `price`: Limit price for execution
- **Special Methods:**
  - `__lt__()`: Implements three-level priority ordering:
    1. Price (reversed for BUY side: higher price = higher priority)
    2. Time (earlier = higher priority)
    3. Size (smaller = higher priority)

### 2. Trade Records ([Trade.py](ordermatchinengine/Trade.py))

**Trade Class:**
Immutable record of executed trades.

**Attributes:**
- `timestamp`: Trade execution time (microseconds)
- `side`: Which side (BUY/SELL) initiated the trade (aggressive order)
- `price`: Execution price (always the resting order's price)
- `size`: Quantity traded
- `incoming_order_id`: ID of the aggressive (incoming) order
- `book_order_id`: ID of the passive (resting) order in the book

### 3. Order Book ([Orderbook.py](ordermatchinengine/Orderbook.py))

The core matching engine that processes orders and maintains the order book.

#### Data Structures

- **`bids`**: SortedList of buy orders (highest price first)
- **`asks`**: SortedList of sell orders (lowest price first)
- **`trades`**: List of all executed trades

Uses `SortedList` from the `sortedcontainers` library for:
- O(log n) insertion and removal
- Automatic maintenance of sorted order
- Critical for high-frequency performance

#### Key Methods

**`process_order(order)` / `process_order_async(order)`**

The heart of the matching engine. Available in both synchronous and asynchronous versions. Processing flow:

1. **Cancel Order Handling:**
   - Searches both `bids` and `asks` for matching `order_id`
   - Removes the order if found
   - Returns immediately

2. **Market/Limit Order Matching:**

   **Step 1: Determine Matching Condition**
   - Uses dynamic `while_clause()` function:
     - BUY limit: Matches if `ask price ≤ bid price`
     - SELL limit: Matches if `bid price ≥ ask price`
     - Market orders: Match if opposite side has orders

   **Step 2: Match Against Best Opposite Order**
   - While matching condition is true:
     - Pop best opposite order from the book
     - Calculate fill based on volume comparison:
       - **Equal volumes:** Both orders completely filled
       - **Incoming larger:** Book order filled, incoming continues
       - **Book order larger:** Incoming filled, book order returned to book
     - Create Trade record (execution price = resting order's price)
     - Update `remaining` quantities

   **Step 3: Handle Unfilled Remainder**
   - Limit orders with remaining quantity → added to book
   - Market orders → never added (execute or die)

**Utility Methods:**
- `get_bid()` / `get_bid_async()`: Returns best bid price (or None if no bids)
- `get_ask()` / `get_ask_async()`: Returns best ask price (or None if no asks)
- `get_spread_async()`: Returns tuple of (bid, ask) atomically with lock protection
- `__len__()`: Total orders in book (bids + asks)
- `__repr__()`: Pretty-prints the order book state with all price levels

## Matching Algorithm Details

### Price-Time Priority Mechanism

The engine implements the standard exchange matching algorithm:

1. **Sorted Order Books:**
   - Bids sorted by price descending (highest first), then time ascending
   - Asks sorted by price ascending (lowest first), then time ascending

2. **Aggressive vs Passive:**
   - **Aggressive orders:** Incoming orders that cross the spread
   - **Passive orders:** Resting orders in the book

3. **Execution Price:**
   - Always the passive (resting) order's price
   - Ensures fairness and price-time priority compliance

4. **Partial Fills:**
   - Supported for all order types
   - Incoming order can match multiple book orders
   - Book orders can be partially filled and remain in book

5. **Order Priority Implementation:**
   ```python
   def __lt__(self, other):
       if self.side == Side.BUY:
           # Higher price = better for buyers
           if self.price != other.price:
               return self.price > other.price
       else:  # SELL
           # Lower price = better for sellers
           if self.price != other.price:
               return self.price < other.price

       # At same price: earlier time wins
       if self.time != other.time:
           return self.time < other.time

       # Tertiary: smaller size wins
       return self.size < other.size
   ```

## Performance Characteristics

### Benchmark Results

**Test Configuration:**
- Hardware: 3 GHz Intel Core i7, 16 GB RAM
- Runtime: PyPy interpreter (recommended for performance)
- Test: 10 million random limit orders (prices: 1-4, sizes: 1-200)

**Single Orderbook (Single Thread):**
- Average processing time: **2.5 microseconds per order**
- Throughput: **~400,000 orders/second**

**Multiple Orderbooks (Parallel Threads):**
- Average processing time: **1.18 microseconds per order**
- Throughput: **850,000+ orders/second**

### Performance Optimizations

1. **SortedList Data Structure:**
   - O(log n) insertions and deletions
   - No manual sorting required
   - Efficient best price retrieval

2. **Microsecond Timestamps:**
   - High precision for time-priority ordering
   - Critical for high-frequency scenarios

3. **PyPy Interpreter:**
   - JIT compilation provides significant speedup
   - Recommended over CPython for production use

4. **Multi-Threading Strategy:**
   - Each orderbook is single-threaded (no locking overhead)
   - Multiple orderbooks can run on separate threads
   - Scales linearly with number of instruments

## Dependencies

From [requirements.txt](requirements.txt):

```
sortedcontainers==2.4.0    # Core dependency for SortedList
pytest==8.3.3              # Testing framework
pytest-asyncio==0.24.0     # Async test support
iniconfig==2.0.0           # pytest dependency
packaging==24.1            # pytest dependency
pluggy==1.5.0              # pytest dependency
```

**Key Dependencies:**
- **sortedcontainers:** Provides the `SortedList` implementation crucial for maintaining sorted order books
- **pytest-asyncio:** Enables testing of async functions with pytest

## Testing

### Unit Tests ([tests/unit/](tests/unit/))

**[test_order.py](tests/unit/test_order.py):**
- Tests order initialization
- Validates all order types: Order, CancelOrder, MarketOrder, LimitOrder
- Checks proper attribute assignment

**[test_orderbook.py](tests/unit/test_orderbook.py):**
- `testInitialState()`: Validates empty orderbook
- `testInsert()`: Tests single order insertion
- `testExecution()`: Tests basic matching of opposing orders
- `testExecution_marmooli()`: Tests partial fills with multiple orders

### Performance Tests ([tests/performance/Benchmark.py](tests/performance/Benchmark.py))

- Processes 10 million random orders
- Measures throughput and latency
- Validates performance claims in README

**Run tests:**
```bash
pytest tests/
```

**Run benchmark:**
```bash
python tests/performance/Benchmark.py
```

## Key Features

### 1. Microsecond Precision
All timestamps use microsecond precision (`int(1e6 * time())`), critical for:
- Accurate time-priority ordering
- High-frequency trading scenarios
- Regulatory compliance

### 2. Three-Level Order Priority
Smart sorting implementation in `LimitOrder.__lt__()`:
- Primary: Price advantage
- Secondary: Time priority (FIFO)
- Tertiary: Size (smaller first)

### 3. Dynamic Matching Conditions
The nested `while_clause()` function elegantly handles:
- BUY limit order matching
- BUY market order matching
- SELL limit order matching
- SELL market order matching

### 4. Comprehensive Partial Fill Handling
Three-way branching for all volume scenarios:
```python
if book_order.remaining == incoming.remaining:
    # Complete fill - both orders done
elif book_order.remaining < incoming.remaining:
    # Book order filled, incoming continues
else:
    # Incoming filled, book order remains
```

### 5. Price Continuity
- Execution always occurs at resting order's price
- Ensures fairness and exchange compliance
- Prevents price manipulation

## Usage Examples

### Basic Synchronous Usage

```python
from ordermatchinengine.Order import Side, LimitOrder, MarketOrder, CancelOrder
from ordermatchinengine.Orderbook import Orderbook

# Create orderbook
book = Orderbook()

# Add limit orders
buy_order = LimitOrder(order_id=1, side=Side.BUY, size=100, price=99.50)
sell_order = LimitOrder(order_id=2, side=Side.SELL, size=100, price=100.50)

book.process_order(buy_order)
book.process_order(sell_order)

# Check spread
print(f"Best bid: {book.get_bid()}")  # 99.50
print(f"Best ask: {book.get_ask()}")  # 100.50

# Market order crosses spread
market_buy = MarketOrder(order_id=3, side=Side.BUY, size=50)
book.process_order(market_buy)

# Check trades
print(f"Trades executed: {len(book.trades)}")  # 1
print(f"Trade price: {book.trades[0].price}")  # 100.50 (seller's price)

# Cancel an order
cancel = CancelOrder(order_id=1)
book.process_order(cancel)
```

### Asynchronous Usage

```python
import asyncio
from ordermatchinengine.Order import Side, LimitOrder
from ordermatchinengine.Orderbook import Orderbook

async def main():
    book = Orderbook()

    # Process orders asynchronously
    await book.process_order_async(LimitOrder(1, Side.BUY, 100, 99.50))
    await book.process_order_async(LimitOrder(2, Side.SELL, 100, 100.50))

    # Get spread atomically
    bid, ask = await book.get_spread_async()
    print(f"Spread: {bid} - {ask}")

    # Concurrent order submission
    await asyncio.gather(
        book.process_order_async(LimitOrder(3, Side.BUY, 50, 100.00)),
        book.process_order_async(LimitOrder(4, Side.BUY, 50, 100.25)),
        book.process_order_async(LimitOrder(5, Side.SELL, 50, 100.75)),
    )

    print(f"Total orders in book: {len(book)}")

asyncio.run(main())
```

### Checking Order Book State

```python
# Pretty print the book
print(book)
# Output shows all price levels with orders

# Get book depth
num_orders = len(book)
print(f"Total orders in book: {num_orders}")
```

## Current Limitations and Potential Enhancements

### Not Currently Implemented

1. **Order ID Management:** No built-in order ID generation or uniqueness validation
2. **Order Book Depth Queries:** No method to query multiple price levels at once
3. **Market Data Feeds:** No snapshot or incremental update methods
4. **Persistence:** No database or log persistence for recovery
5. **Input Validation:** Limited validation for order parameters (price, size)
6. **Stop Orders:** Stop-loss and stop-limit orders not implemented
7. **Time-in-Force:** GTC, IOC, FOK order types not implemented
8. **Circuit Breakers:** No price limit checks or volatility controls
9. **Order Modification:** No modify order functionality (must cancel and replace)
10. **Position Tracking:** No account or position management

### Potential Enhancement Areas

1. **Add order book depth methods** (e.g., get top N levels)
2. **Implement stop orders** and advanced order types
3. **Add market data snapshot/delta methods** for feeds
4. **Implement persistence layer** for crash recovery
5. **Add input validation and error handling**
6. **Implement risk controls** (price bands, circuit breakers)
7. **Add order modify functionality**
8. **Support iceberg/hidden orders**
9. **Add trade reporting and audit trail**
10. **Implement FIX protocol interface**

## Domain Concepts

### Order Matching Fundamentals

**Order Book Structure:**
- **Two-sided market:** Bids (buy orders) and Asks (sell orders)
- **Spread:** Difference between best bid and best ask
- **Depth:** Number of orders at each price level
- **Liquidity:** Total volume available at various price levels

**Order Flow:**
- **Liquidity Providers:** Submit limit orders (passive)
- **Liquidity Takers:** Submit market orders (aggressive)
- **Crossing the spread:** When buy price ≥ ask price or sell price ≤ bid price

**Trade Execution:**
- Each match generates a Trade record
- Tracks both sides of the transaction
- Execution price is always the passive order's price
- Partial fills are supported and tracked

## Development Notes

### Python Version Requirements

This project requires **Python 3.11+** for:
- `typing.Self` type hint
- Union type syntax with `|` operator
- Modern `list[T]` and `tuple[T, ...]` generic syntax

### Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (including async tests)
pytest tests/

# Run benchmark
python tests/performance/Benchmark.py
```

### Running with PyPy

For maximum performance, use PyPy instead of CPython:

```bash
# Install PyPy
brew install pypy3  # macOS
# or download from pypy.org

# Install dependencies
pypy3 -m pip install -r requirements.txt

# Run benchmark
pypy3 tests/performance/Benchmark.py
```

### Code Style

The codebase follows Python conventions:
- Snake_case for variables and functions
- PascalCase for classes
- Minimal comments (code is self-documenting)
- Clear, descriptive naming

### Git Status

**Current Branch:** main
**Status:** Clean working directory
**Recent Activity:**
- Added .gitignore
- Updated packages
- Refactored to use snake_case
- Module renaming

## License

MIT License - Copyright 2020 Lalit Vavdara

See [LICENSE](LICENSE) for full text.

## Quick Reference

### Order Processing Flow

```
1. Order arrives → process_order()
2. If CancelOrder → Remove from book → Done
3. If Market/Limit → Check matching condition
4. While can match:
   a. Pop best opposite order
   b. Calculate fill (min of both remaining)
   c. Create Trade record
   d. Update remaining quantities
   e. If book order has remaining, add back to book
5. If incoming has remaining and is LimitOrder → Add to book
6. Done
```

### Key Constants

- **Timestamp precision:** Microseconds (`int(1e6 * time())`)
- **Side values:** BUY=0, SELL=1
- **Price priority:** BUY high-to-low, SELL low-to-high
- **Time priority:** FIFO (first in, first out)

### Performance Targets

- Single thread: 400,000 orders/sec
- Multi-thread: 850,000+ orders/sec
- Latency: 1-3 microseconds per order

---

**Documentation Generated:** 2025-11-20
**Python Version:** 3.11+
**Async Support:** Yes
