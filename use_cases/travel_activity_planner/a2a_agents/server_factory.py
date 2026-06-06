import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import uvicorn
from starlette.applications import Starlette
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore


def create_app(agent_card, executor_class) -> Starlette:
    """Build a Starlette A2A application for the given agent card and executor."""
    handler = DefaultRequestHandler(
        agent_executor=executor_class(),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(agent_card=agent_card, http_handler=handler).build(
        rpc_url='/'
    )


def run(agent_card, executor_class, port: int) -> None:
    """Create the app and start the uvicorn server."""
    app = create_app(agent_card, executor_class)
    uvicorn.run(app, host='0.0.0.0', port=port)
