"""
Simple Pipeline Example

Demonstrates basic sequential workflow with Bridgic ASL.
"""

from bridgic.asl import ASLAutoma, graph


# Define worker functions
async def validate_input(text: str) -> str:
    """Validate and clean input text."""
    if not text or not text.strip():
        raise ValueError("Input cannot be empty")
    return text.strip()


async def transform_text(text: str) -> str:
    """Transform the text (uppercase in this example)."""
    return text.upper()


async def add_metadata(text: str) -> dict:
    """Add metadata to the result."""
    return {
        "original_length": len(text),
        "transformed": text,
        "word_count": len(text.split())
    }


# Define the pipeline using ASL
class TextProcessingPipeline(ASLAutoma):
    """A simple text processing pipeline."""

    with graph as g:
        # Assign workers
        validate = validate_input
        transform = transform_text
        enrich = add_metadata

        # Define flow: validate -> transform -> enrich
        # + marks start, ~ marks output
        +validate >> transform >> ~enrich


# Usage
async def main():
    # Create pipeline instance
    pipeline = TextProcessingPipeline()

    # Run the pipeline
    result = await pipeline.arun(text="  hello world  ")

    print(f"Result: {result}")
    # Output: {'original_length': 11, 'transformed': 'HELLO WORLD', 'word_count': 2}


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
