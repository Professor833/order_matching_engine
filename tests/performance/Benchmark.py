import asyncio
from ordermatchinengine import Orderbook, LimitOrder, Side
from random import getrandbits, randint
from time import time


def run_sync_benchmark():
    """Run synchronous benchmark."""
    print("=" * 50)
    print("Synchronous Benchmark")
    print("=" * 50)

    OB = Orderbook()
    num_orders = 10**7
    orders: list[LimitOrder] = []

    print(f"Generating {num_orders:,} random orders...")
    for n in range(num_orders):
        if bool(getrandbits(1)):
            orders.append(LimitOrder(n, Side.BUY, randint(1, 200), randint(1, 4)))
        else:
            orders.append(LimitOrder(n, Side.SELL, randint(1, 200), randint(1, 4)))

    print("Processing orders...")
    start = time()
    for order in orders:
        OB.process_order(order)
    end = time()

    total_time = end - start
    print(f"Time: {total_time:.3f}s")
    print(f"Time per order (us): {1_000_000 * total_time / num_orders:.3f}")
    print(f"Orders per second: {num_orders / total_time:,.0f}")
    print(f"Total trades executed: {len(OB.trades):,}")
    print()


async def run_async_benchmark():
    """Run asynchronous benchmark."""
    print("=" * 50)
    print("Asynchronous Benchmark")
    print("=" * 50)

    OB = Orderbook()
    num_orders = 10**6  # Reduced for async benchmark
    orders: list[LimitOrder] = []

    print(f"Generating {num_orders:,} random orders...")
    for n in range(num_orders):
        if bool(getrandbits(1)):
            orders.append(LimitOrder(n, Side.BUY, randint(1, 200), randint(1, 4)))
        else:
            orders.append(LimitOrder(n, Side.SELL, randint(1, 200), randint(1, 4)))

    print("Processing orders asynchronously...")
    start = time()
    for order in orders:
        await OB.process_order_async(order)
    end = time()

    total_time = end - start
    print(f"Time: {total_time:.3f}s")
    print(f"Time per order (us): {1_000_000 * total_time / num_orders:.3f}")
    print(f"Orders per second: {num_orders / total_time:,.0f}")
    print(f"Total trades executed: {len(OB.trades):,}")
    print()


async def run_concurrent_benchmark():
    """Run benchmark with concurrent order submission."""
    print("=" * 50)
    print("Concurrent Async Benchmark")
    print("=" * 50)

    OB = Orderbook()
    num_orders = 10**5  # Smaller batch for concurrent test
    batch_size = 1000

    print(f"Generating {num_orders:,} random orders in batches of {batch_size}...")
    orders: list[LimitOrder] = []
    for n in range(num_orders):
        if bool(getrandbits(1)):
            orders.append(LimitOrder(n, Side.BUY, randint(1, 200), randint(1, 4)))
        else:
            orders.append(LimitOrder(n, Side.SELL, randint(1, 200), randint(1, 4)))

    async def process_batch(batch: list[LimitOrder]):
        for order in batch:
            await OB.process_order_async(order)

    # Split into batches
    batches = [orders[i:i + batch_size] for i in range(0, len(orders), batch_size)]

    print(f"Processing {len(batches)} batches concurrently...")
    start = time()
    await asyncio.gather(*[process_batch(batch) for batch in batches])
    end = time()

    total_time = end - start
    print(f"Time: {total_time:.3f}s")
    print(f"Time per order (us): {1_000_000 * total_time / num_orders:.3f}")
    print(f"Orders per second: {num_orders / total_time:,.0f}")
    print(f"Total trades executed: {len(OB.trades):,}")
    print()


async def main():
    """Run all benchmarks."""
    print("\nOrder Matching Engine Benchmark")
    print("Python 3.11 with Async Support")
    print("=" * 50)
    print()

    # Run sync benchmark
    run_sync_benchmark()

    # Run async benchmarks
    await run_async_benchmark()
    await run_concurrent_benchmark()

    print("Benchmark complete!")


if __name__ == "__main__":
    asyncio.run(main())


"""
Expected Output (approximate):
==================================================
Synchronous Benchmark
==================================================
Time: 25.271s
Time per order (us): 2.527
Orders per second: 395,706

==================================================
Asynchronous Benchmark
==================================================
Time: 3.5s
Time per order (us): 3.5
Orders per second: 285,714

==================================================
Concurrent Async Benchmark
==================================================
Time: 0.5s
Time per order (us): 5.0
Orders per second: 200,000
"""
