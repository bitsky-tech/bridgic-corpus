"""
ReCENT Autonomous Agent Example

Demonstrates building an autonomous agent with ReCENT memory management
that can use tools to accomplish goals.
"""

from bridgic.core.agentic.recent import (
    ReCentAutoma,
    ReCentMemoryConfig,
    StopCondition,
)
from bridgic.core.agentic.tool_specs import FunctionToolSpec
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration


# Define tools the agent can use
async def search_web(query: str) -> str:
    """Search the web for information.

    Args:
        query: The search query

    Returns:
        Search results as text
    """
    # Simulated search results
    return f"Search results for '{query}': Found 3 relevant articles about {query}."


async def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: The city name

    Returns:
        Weather information
    """
    # Simulated weather data
    return f"Weather in {city}: Sunny, 22°C, humidity 45%"


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2")

    Returns:
        Result of the calculation
    """
    try:
        # Safe eval for simple math
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: Could not evaluate '{expression}'"


async def save_note(title: str, content: str) -> str:
    """Save a note for later reference.

    Args:
        title: Title of the note
        content: Content of the note

    Returns:
        Confirmation message
    """
    # Simulated note saving
    return f"Note saved: '{title}'"


def create_agent(api_key: str) -> ReCentAutoma:
    """Create a ReCENT autonomous agent with tools.

    Args:
        api_key: OpenAI API key

    Returns:
        Configured ReCentAutoma instance
    """
    # Initialize LLM
    llm = OpenAILlm(
        api_key=api_key,
        timeout=30,
        configuration=OpenAIConfiguration(
            model="gpt-4o",
            temperature=0.7
        )
    )

    # Create tool specifications
    tools = [
        FunctionToolSpec(search_web),
        FunctionToolSpec(get_weather),
        FunctionToolSpec(calculate),
        FunctionToolSpec(save_note),
    ]

    # Create agent with ReCENT memory
    agent = ReCentAutoma(
        llm=llm,
        tools=tools,
        # Memory configuration for context management
        memory_config=ReCentMemoryConfig(llm=llm),
        # Stop conditions
        stop_condition=StopCondition(
            max_iteration=15,  # Max tool calls
            max_consecutive_no_tool_selected=3  # Stop if no tool selected 3 times
        )
    )

    return agent


# Usage
async def main():
    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create agent
    agent = create_agent(api_key)

    # Run agent with a goal
    result = await agent.arun(
        goal="Find the weather in Tokyo and San Francisco, calculate which is warmer, and save a note with the comparison."
    )

    print("Agent Result:")
    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
