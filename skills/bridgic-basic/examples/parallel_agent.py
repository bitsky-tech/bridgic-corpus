"""
Parallel Agent Example

Demonstrates fan-out/fan-in pattern with concurrent execution.
"""

from bridgic.asl import ASLAutoma, graph, Settings
from bridgic.core.automa.args import ArgsMappingRule


# Simulated search functions
async def keyword_search(query: str) -> list[dict]:
    """Search using keyword matching."""
    # Simulated results
    return [
        {"source": "keyword", "title": f"Keyword result for: {query}", "score": 0.8}
    ]


async def semantic_search(query: str) -> list[dict]:
    """Search using semantic similarity."""
    # Simulated results
    return [
        {"source": "semantic", "title": f"Semantic result for: {query}", "score": 0.9}
    ]


async def database_search(query: str) -> list[dict]:
    """Search in database."""
    # Simulated results
    return [
        {"source": "database", "title": f"DB result for: {query}", "score": 0.7}
    ]


async def merge_and_rank(results: list) -> list[dict]:
    """Merge results from all sources and rank by score."""
    # results is a list of results from each parallel worker: [[...], [...], [...]]
    all_results = []
    for source_results in results:
        all_results.extend(source_results)

    # Sort by score descending
    ranked = sorted(all_results, key=lambda x: x["score"], reverse=True)
    return ranked


# Define parallel search agent
class ParallelSearchAgent(ASLAutoma):
    """Search agent that queries multiple sources in parallel."""

    with graph as g:
        # Three parallel search paths
        keyword = keyword_search
        semantic = semantic_search
        database = database_search

        # Merge results (needs MERGE rule to receive list of all inputs)
        merge = merge_and_rank * Settings(args_mapping_rule=ArgsMappingRule.MERGE)

        # Flow: all three searches run in parallel, then merge
        +(keyword & semantic & database) >> ~merge


# Usage
async def main():
    agent = ParallelSearchAgent()

    # All three searches run concurrently
    results = await agent.arun(query="machine learning tutorials")

    print("Ranked Results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. [{result['source']}] {result['title']} (score: {result['score']})")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
