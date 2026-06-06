from uuid import uuid4
import asyncio
import httpx

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (
    Message,
    Part,
    TextPart,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)


def _part_text(p: Part) -> str:
    if hasattr(p, 'root') and hasattr(p.root, 'text'):
        return p.root.text or ""
    return ""


async def main():
    base_url = 'http://localhost:8080'

    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client = ClientFactory(ClientConfig(httpx_client=httpx_client)).create(agent_card)

        print("Main Agent: Enter text or 'exit' to quit\n")

        while True:
            user_input = input("User:")
            if user_input.strip().lower() == "exit":
                break

            msg = Message(
                message_id=str(uuid4()),
                role=Role.user,
                parts=[
                    Part(root=TextPart(text=user_input)),
                    Part(root=TextPart(text='Sent from: MainRouterAgent')),
                ],
            )

            async for event in client.send_message(msg):
                if isinstance(event, tuple):
                    task, update = event
                    if isinstance(task, Task):
                        print(f"Task initialised: {task.id}")
                    if isinstance(update, TaskStatusUpdateEvent):
                        print(f"Main Agent [status]: {update.status.state}")
                        if update.status.message and update.status.message.parts:
                            print(f"{_part_text(update.status.message.parts[0])}")
                    elif isinstance(update, TaskArtifactUpdateEvent):
                        text = _part_text(update.artifact.parts[0]) if update.artifact.parts else ""
                        if text:
                            print(f"Main Agent: {text}")
                elif isinstance(event, Message):
                    text = _part_text(event.parts[0]) if event.parts else ""
                    if text:
                        print(f"Main Agent: {text}")
                else:
                    print(f"Unhandled response: {event}")

if __name__ == '__main__':
    asyncio.run(main())
