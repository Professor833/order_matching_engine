# Order Matching Engine

A high-performance order matching engine implemented in Python, designed to process buy and sell orders using a price-time priority algorithm.

**Author:** Lalit Vavdara
**License:** MIT
**Python:** 3.11+
**Status:** Work in Progress

## Features

- **Price-Time Priority Matching:** Standard exchange matching algorithm
- **Async/Await Support:** Full asynchronous order processing with `asyncio`
- **Thread-Safe Operations:** Lock-protected async methods
- **Multi-Process Scaling:** True parallelism with ProcessPoolExecutor (bypasses GIL)
- **Modern Python:** Type hints with `Self`, union types, generics

## Performance Benchmarks

### Single Thread Performance

| Metric | CPython 3.12 | PyPy (Expected) |
|--------|-------------|-----------------|
| Throughput | ~370,000 orders/sec | ~800,000 orders/sec |
| Latency | 2.7 µs/order | ~1.2 µs/order |
| P99 Latency | 1.49 µs/order | <1.5 µs/order |

### Multi-Process Performance (12 Parallel Orderbooks)

| Metric | CPython 3.12 | PyPy (Expected) |
|--------|-------------|-----------------|
| Aggregate Throughput | **1,626,583 orders/sec** | ~4,000,000+ orders/sec |
| Per-Order Latency | 0.62 µs/order | ~0.25 µs/order |

### Latency Percentiles

| Percentile | Latency |
|------------|---------|
| P50 | 1.38 µs |
| P95 | 1.45 µs |
| P99 | 1.49 µs |

Benchmarks run on Apple M-series (12 cores), Python 3.12.9

## AWS EC2 Recommendations

### Recommended Instance Types

| Use Case | Instance | vCPUs | Hourly Cost | Notes |
|----------|----------|-------|-------------|-------|
| Development | c7i.xlarge | 4 | $0.17 | Good for testing |
| Production | c7i.2xlarge | 8 | $0.34 | Balanced performance |
| High-Scale | c7i.4xlarge | 16 | $0.68 | Multiple orderbooks |
| Cost-Optimized | c7g.2xlarge | 8 | $0.29 | ARM/Graviton3 |

### Performance Tuning for EC2

```bash
# Environment variables for optimal performance
export PYTHONOPTIMIZE=2          # Remove asserts and docstrings
export PYTHONDONTWRITEBYTECODE=1 # Don't create .pyc files
export PYTHONHASHSEED=0          # Deterministic hashing
export MALLOC_ARENA_MAX=2        # Reduce memory fragmentation

# Pin process to single CPU core (Linux)
taskset -c 0 python tests/performance/Benchmark.py

# Use PyPy for 2-3x performance boost
pypy3 tests/performance/Benchmark.py
```

### Expected EC2 Performance (c7i.2xlarge)

| Benchmark | Throughput | Latency |
|-----------|------------|---------|
| Single-thread | 400,000-500,000 orders/sec | 2.0-2.5 µs |
| Multi-process (8 books) | 2,000,000-3,000,000 orders/sec | 0.3-0.5 µs |
| P99 Latency | - | ~3.0 µs |

With PyPy on c7i.2xlarge:

- Single-thread: **800,000+ orders/sec**
- Multi-process: **4,000,000+ orders/sec**

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/order-matching-engine.git
cd order-matching-engine

# Create virtual environment (Python 3.11+)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from ordermatchinengine import Orderbook, LimitOrder, MarketOrder, CancelOrder, Side

# Create orderbook
book = Orderbook()

# Add limit orders
book.process_order(LimitOrder(order_id=1, side=Side.BUY, size=100, price=99.50))
book.process_order(LimitOrder(order_id=2, side=Side.SELL, size=100, price=100.50))

# Check spread
print(f"Bid: {book.get_bid()}, Ask: {book.get_ask()}")

# Execute market order
book.process_order(MarketOrder(order_id=3, side=Side.BUY, size=50))

# View trades
print(f"Trades: {len(book.trades)}")
for trade in book.trades:
    print(f"  Price: {trade.price}, Size: {trade.size}")

# Cancel an order
book.process_order(CancelOrder(order_id=1))
```

### Async Usage

```python
import asyncio
from ordermatchinengine import Orderbook, LimitOrder, Side

async def main():
    book = Orderbook()

    # Process orders asynchronously
    await book.process_order_async(LimitOrder(1, Side.BUY, 100, 99.50))
    await book.process_order_async(LimitOrder(2, Side.SELL, 100, 100.50))

    # Get spread atomically (thread-safe)
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

## Running Tests

### Unit Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
PYTHONPATH=. pytest tests/

# Run with verbose output
PYTHONPATH=. pytest tests/ -v

# Run specific test file
PYTHONPATH=. pytest tests/unit/test_orderbook.py -v

# Run with coverage (requires pytest-cov)
PYTHONPATH=. pytest tests/ --cov=ordermatchinengine
```

### Test Files

- `tests/unit/test_order.py` - Order class tests (initialization, attributes)
- `tests/unit/test_orderbook.py` - Orderbook tests (matching, execution, cancellation)

## Running Benchmarks

### Quick Benchmark

```bash
# Activate virtual environment
source venv/bin/activate

# Run full benchmark suite
PYTHONPATH=. python tests/performance/Benchmark.py
```

### Benchmark with PyPy (Recommended for Production)

```bash
# Install PyPy
brew install pypy3  # macOS
# or download from pypy.org

# Install dependencies in PyPy
pypy3 -m pip install sortedcontainers

# Run benchmark
PYTHONPATH=. pypy3 tests/performance/Benchmark.py
```

### Benchmark Options

The benchmark runs several tests:

1. **Synchronous Benchmark** - Single-thread baseline (10M orders)
2. **Multi-Process Benchmark** - Parallel orderbooks using all CPU cores
3. **Latency Benchmark** - P50/P95/P99 percentile analysis
4. **Async Benchmark** - Asynchronous processing performance
5. **Market Scenarios** - Different market conditions (wide/tight spread)

### Expected Output

```text
============================================================
BENCHMARK SUMMARY
============================================================
Single-thread throughput: 372,783 orders/sec
Multi-process throughput: 1,626,583 orders/sec
Async throughput:         350,348 orders/sec
P99 latency:              1.486 µs/order
```

## Architecture

### Core Components

- **Order.py** - Order types (LimitOrder, MarketOrder, CancelOrder)
- **Orderbook.py** - Matching engine with price-time priority
- **Trade.py** - Trade execution records

### Order Types

| Type | Description |
|------|-------------|
| `LimitOrder` | Execute at specified price or better |
| `MarketOrder` | Execute immediately at best available price |
| `CancelOrder` | Remove existing order from book |

### Matching Algorithm

1. **Price Priority:** Better prices execute first (higher bids, lower asks)
2. **Time Priority:** Earlier orders at same price execute first (FIFO)
3. **Size Priority:** Smaller orders as tertiary tiebreaker

### Data Structures

Uses `SortedList` from `sortedcontainers` for O(log n) operations:

- Bids: Sorted by price descending (highest first)
- Asks: Sorted by price ascending (lowest first)

### Trade Execution

- Execution price is always the **resting order's price** (passive side)
- Partial fills are fully supported
- Each match generates a `Trade` record with:
  - `timestamp` - Execution time (microseconds)
  - `price` - Execution price
  - `size` - Quantity traded
  - `incoming_order_id` - Aggressive order
  - `book_order_id` - Passive order

## Project Structure

```text
order-matching-engine/
├── ordermatchinengine/
│   ├── __init__.py
│   ├── Order.py          # Order class hierarchy
│   ├── Orderbook.py      # Core matching engine
│   └── Trade.py          # Trade records
├── tests/
│   ├── unit/
│   │   ├── test_order.py
│   │   └── test_orderbook.py
│   └── performance/
│       └── Benchmark.py  # Performance benchmarks
├── requirements.txt
├── LICENSE
├── CLAUDE.md             # AI assistant documentation
└── README.md
```

## API Reference

### Orderbook

```python
class Orderbook:
    # Synchronous methods
    def process_order(self, order: Order) -> None
    def get_bid(self) -> float | None
    def get_ask(self) -> float | None

    # Asynchronous methods (thread-safe)
    async def process_order_async(self, order: Order) -> None
    async def get_bid_async(self) -> float | None
    async def get_ask_async(self) -> float | None
    async def get_spread_async(self) -> tuple[float | None, float | None]

    # Properties
    trades: list[Trade]  # All executed trades
    bids: SortedList      # Buy orders
    asks: SortedList      # Sell orders
```

### Order Classes

```python
# Limit Order
LimitOrder(order_id: int, side: Side, size: int, price: float)

# Market Order
MarketOrder(order_id: int, side: Side, size: int)

# Cancel Order
CancelOrder(order_id: int)

# Side Enum
class Side(Enum):
    BUY = 0
    SELL = 1
```

### Trade

```python
@dataclass
class Trade:
    timestamp: int          # Microseconds
    side: Side              # Aggressive side
    price: float            # Execution price
    size: int               # Quantity
    incoming_order_id: int  # Taker order
    book_order_id: int      # Maker order
```

## Dependencies

- `sortedcontainers==2.4.0` - Sorted data structures
- `pytest==8.3.3` - Testing framework
- `pytest-asyncio==0.24.0` - Async test support

## Performance Notes

### Why Multi-Process vs Multi-Thread?

Python's Global Interpreter Lock (GIL) prevents true parallel execution in threads. The benchmark uses `ProcessPoolExecutor` to:

- Bypass GIL limitations
- Achieve true CPU parallelism
- Scale linearly with CPU cores

### Optimization Tips

1. **Use PyPy** - 2-3x faster than CPython
2. **Disable GC** - Benchmark does this automatically
3. **CPU Pinning** - Use `taskset` on Linux for consistent results
4. **Warm-up** - First run warms up Python's adaptive optimizations

## Current Limitations

- No order ID uniqueness validation
- No order modification (must cancel and replace)
- No stop orders or advanced order types
- No persistence layer
- No market data feed interfaces

## License

MIT License - Copyright 2025 Lalit Vavdara

See [LICENSE](LICENSE) for full text.
