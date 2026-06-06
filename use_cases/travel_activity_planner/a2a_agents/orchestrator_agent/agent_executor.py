import uuid
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart, TaskArtifactUpdateEvent, TaskStatusUpdateEvent, Message
from .agent_logic import OrchestratorAgentLogic


def _make_part(text: str) -> Part:
    return Part(root=TextPart(text=str(text)))


def _part_text(p: Part) -> str:
    """Extract text from a Part regardless of inner type."""
    if hasattr(p, 'root') and hasattr(p.root, 'text'):
        return p.root.text or ""
    return ""


class AgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = OrchestratorAgentLogic()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        async for response in self.agent.stream(context.get_user_input(), context_id=context.context_id):

            if isinstance(response, dict):
                completed      = response.get("completed", False)
                failed         = response.get("failed", False)
                input_required = response.get("input_required", False)
                content        = response.get("content", "")

                if failed:
                    await updater.failed(updater.new_agent_message(parts=[_make_part(content)]))
                    return
                elif input_required:
                    await updater.requires_input(updater.new_agent_message(parts=[_make_part(content)]))
                elif completed:
                    if content:
                        await updater.add_artifact(parts=[_make_part(content)], name="response")
                    await updater.complete()
                    return
                else:
                    if content:
                        await updater.add_artifact(parts=[_make_part(content)], name="response")

            elif isinstance(response, TaskArtifactUpdateEvent):
                if response.artifact and response.artifact.parts:
                    await updater.add_artifact(
                        name="response",
                        parts=list(response.artifact.parts),
                        artifact_id=str(uuid.uuid4()),
                    )

            elif isinstance(response, TaskStatusUpdateEvent):
                if response.status.state == "failed":
                    error_text = "Remote agent failed"
                    if response.status.message and response.status.message.parts:
                        error_text = _part_text(response.status.message.parts[0]) or error_text
                    await updater.failed(updater.new_agent_message(parts=[_make_part(error_text)]))
                    return
                if response.status.message and response.status.message.parts:
                    text = _part_text(response.status.message.parts[0])
                    if text:
                        await updater.add_artifact(
                            name="status",
                            parts=[_make_part(text)],
                            artifact_id=str(uuid.uuid4()),
                        )

            elif isinstance(response, Message):
                if response.parts:
                    await updater.add_artifact(
                        name="response",
                        parts=list(response.parts),
                        artifact_id=str(uuid.uuid4()),
                    )

        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')
