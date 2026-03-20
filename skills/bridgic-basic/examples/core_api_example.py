"""
Core API Example with @worker Decorator

Demonstrates using GraphAutoma directly with the @worker decorator
for lower-level control compared to ASL syntax.
"""

import asyncio
from bridgic.core.automa import GraphAutoma, worker


class DataProcessingAutoma(GraphAutoma):
    """A simple data processing workflow using Core API."""

    @worker(is_start=True)
    async def fetch_data(self, source: str) -> dict:
        """Fetch data from a source."""
        # Simulated data fetch
        return {
            "source": source,
            "records": [
                {"id": 1, "value": 10},
                {"id": 2, "value": 20},
                {"id": 3, "value": 30},
            ]
        }

    @worker(dependencies=["fetch_data"])
    async def validate_data(self, data: dict) -> dict:
        """Validate the fetched data."""
        valid_records = [
            r for r in data["records"]
            if r["value"] > 0
        ]
        return {
            **data,
            "records": valid_records,
            "valid_count": len(valid_records)
        }

    @worker(dependencies=["validate_data"])
    async def transform_data(self, data: dict) -> dict:
        """Transform the validated data."""
        transformed = [
            {**r, "value": r["value"] * 2}
            for r in data["records"]
        ]
        return {
            **data,
            "records": transformed,
            "transformed": True
        }

    @worker(dependencies=["transform_data"], is_output=True)
    async def summarize(self, data: dict) -> dict:
        """Create a summary of the processed data."""
        total = sum(r["value"] for r in data["records"])
        return {
            "source": data["source"],
            "record_count": len(data["records"]),
            "total_value": total,
            "average_value": total / len(data["records"]) if data["records"] else 0
        }


class ParallelFetchAutoma(GraphAutoma):
    """Demonstrates parallel workers with fan-in pattern."""

    @worker(is_start=True)
    async def fetch_users(self) -> list:
        """Fetch user data."""
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    @worker(is_start=True)
    async def fetch_products(self) -> list:
        """Fetch product data."""
        return [{"id": 101, "name": "Widget"}, {"id": 102, "name": "Gadget"}]

    @worker(is_start=True)
    async def fetch_orders(self) -> list:
        """Fetch order data."""
        return [{"id": 1001, "user_id": 1, "product_id": 101}]

    @worker(
        dependencies=["fetch_users", "fetch_products", "fetch_orders"],
        is_output=True
    )
    async def combine_data(
        self,
        users: list,
        products: list,
        orders: list
    ) -> dict:
        """Combine all fetched data."""
        return {
            "users": users,
            "products": products,
            "orders": orders,
            "summary": {
                "user_count": len(users),
                "product_count": len(products),
                "order_count": len(orders)
            }
        }


class DynamicWorkflowAutoma(GraphAutoma):
    """Demonstrates dynamic worker addition at runtime."""

    @worker(is_start=True)
    async def initialize(self, task_count: int) -> int:
        """Initialize and dynamically add workers."""
        # Dynamically add task workers
        for i in range(task_count):
            self.add_func_as_worker(
                key=f"task_{i}",
                func=self._create_task_handler(i),
                dependencies=["initialize"]
            )

        # Add collector that depends on all tasks
        task_keys = [f"task_{i}" for i in range(task_count)]
        self.add_func_as_worker(
            key="collect",
            func=self._collector,
            dependencies=task_keys,
            is_output=True
        )
        return task_count

    def _create_task_handler(self, task_id: int):
        """Create a task handler function."""
        async def handler(count: int) -> dict:
            return {
                "task_id": task_id,
                "processed": True,
                "input_count": count
            }
        return handler

    @staticmethod
    async def _collector(*results) -> list:
        """Collect results from all dynamic tasks."""
        return list(results)


async def main():
    # Example 1: Simple sequential workflow
    print("=== Sequential Data Processing ===")
    processor = DataProcessingAutoma(name="data-processor")
    result = await processor.arun(source="database")
    print(f"Result: {result}")
    print()

    # Example 2: Parallel fetch with fan-in
    print("=== Parallel Fetch ===")
    fetcher = ParallelFetchAutoma(name="parallel-fetcher")
    result = await fetcher.arun()
    print(f"Result: {result}")
    print()

    # Example 3: Dynamic workflow
    print("=== Dynamic Workflow ===")
    dynamic = DynamicWorkflowAutoma(name="dynamic-workflow")
    result = await dynamic.arun(task_count=3)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
