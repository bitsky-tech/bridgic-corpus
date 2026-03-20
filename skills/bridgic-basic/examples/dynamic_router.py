"""
Dynamic Router Example

Demonstrates conditional routing using ferry_to() for runtime decisions.
"""

from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import GraphAutoma
from bridgic.core.automa.args import System


# Router function that decides path at runtime
async def classify_and_route(
    request: dict,
    automa: GraphAutoma = System("automa")
) -> dict:
    """Classify request and route to appropriate handler."""
    request_type = request.get("type", "unknown")
    priority = request.get("priority", "normal")

    # High priority goes to fast path
    if priority == "high":
        automa.ferry_to("fast_handler", request=request)
    # Route by type
    elif request_type == "text":
        automa.ferry_to("text_handler", request=request)
    elif request_type == "image":
        automa.ferry_to("image_handler", request=request)
    else:
        automa.ferry_to("default_handler", request=request)

    return request


# Handler functions - each returns a formatted response
async def handle_fast(request: dict) -> dict:
    """Fast path for high priority requests."""
    return {
        "status": "completed",
        "path": "fast",
        "request": request,
        "formatted": True
    }


async def handle_text(request: dict) -> dict:
    """Handle text requests."""
    return {
        "status": "completed",
        "path": "text",
        "processed": request.get("content", "").upper(),
        "formatted": True
    }


async def handle_image(request: dict) -> dict:
    """Handle image requests."""
    return {
        "status": "completed",
        "path": "image",
        "dimensions": "processed",
        "formatted": True
    }


async def handle_default(request: dict) -> dict:
    """Handle unknown request types."""
    return {
        "status": "completed",
        "path": "default",
        "message": "Handled by default path",
        "formatted": True
    }


# Dynamic routing agent
class RequestRouterAgent(ASLAutoma):
    """Agent that routes requests to appropriate handlers based on type and priority.

    The router uses ferry_to() to dynamically jump to the appropriate handler.
    Each handler is marked as an output (~), so whichever one runs will produce the result.
    """

    with graph as g:
        # Entry point - classifies and routes via ferry_to
        router = classify_and_route

        # Various handlers (only one will be called per request)
        # Each is marked as output since ferry_to jumps directly to them
        fast_handler = handle_fast
        text_handler = handle_text
        image_handler = handle_image
        default_handler = handle_default

        # Flow declaration:
        # - router is start (+)
        # - all handlers are outputs (~) - only the one ferry_to'd to will run
        +router, ~fast_handler, ~text_handler, ~image_handler, ~default_handler


# Usage
async def main():
    agent = RequestRouterAgent()

    # Test different request types
    requests = [
        {"type": "text", "content": "hello world"},
        {"type": "image", "url": "image.png"},
        {"type": "unknown", "data": "..."},
        {"type": "text", "content": "urgent!", "priority": "high"},
    ]

    for request in requests:
        result = await agent.arun(request=request)
        print(f"Request: {request}")
        print(f"Result: {result}")
        print("-" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
