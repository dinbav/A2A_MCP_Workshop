import uuid
from a2a.server.agent_execution import AgentExecutor as BaseA2AExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskArtifactUpdateEvent, TaskState, TaskStatusUpdateEvent, TextPart
from a2a.utils.artifact import new_text_artifact
from a2a.utils.message import new_agent_text_message
from .agent_logic import OrchestratorAgentLogic


class AgentExecutor(BaseA2AExecutor):
    def __init__(self):
        self.agent = OrchestratorAgentLogic()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        updater = TaskUpdater(event_queue, task_id, context_id)
        submitted_sent = False

        def _safe_text(value: str) -> str:
            # Guard against lone surrogate characters that break UTF-8 serialization.
            return str(value).encode("utf-8", errors="replace").decode("utf-8", errors="replace")

        def _extract_part_text(part) -> str | None:
            text = getattr(part, "text", None)
            if not text and hasattr(part, "root"):
                text = getattr(part.root, "text", None)
            if not text and hasattr(part, "model_dump"):
                dumped = part.model_dump()
                if isinstance(dumped, dict):
                    text = dumped.get("text")
            return text

        def _sanitize_parts(parts):
            sanitized = []
            for p in parts or []:
                text = _extract_part_text(p)
                if text is not None:
                    sanitized.append(TextPart(text=_safe_text(text)))
                else:
                    sanitized.append(p)
            return sanitized

        async for response in self.agent.stream(context.get_user_input(), context_id=context.context_id):

            if isinstance(response, dict):
                completed      = response.get("completed", False)
                failed         = response.get("failed", False)
                input_required = response.get("input_required", False)
                content        = response.get("content", "")
                artifact_name  = response.get("artifact_name", "response")
                event_type     = response.get("event_type", "artifact")
                status_state   = response.get("status_state", "working")

                if failed:
                    message = new_agent_text_message(text=_safe_text(content), context_id=context_id, task_id=task_id)
                    await updater.failed(message)
                    return
                elif input_required:
                    message = new_agent_text_message(text=_safe_text(content), context_id=context_id, task_id=task_id)
                    await updater.requires_input(message)
                elif event_type == "status":
                    safe_content = _safe_text(content)
                    message = (
                        new_agent_text_message(text=safe_content, context_id=context_id, task_id=task_id)
                        if safe_content
                        else None
                    )

                    if status_state == "submitted":
                        if not submitted_sent:
                            await updater.submit(message)
                            submitted_sent = True
                        elif message:
                            await updater.update_status(TaskState.submitted, message)
                        continue

                    if status_state == "working":
                        if not submitted_sent:
                            await updater.submit()
                            submitted_sent = True
                        if message:
                            await updater.update_status(TaskState.working, message)
                        continue

                    if status_state == "completed":
                        await updater.complete(message)
                        return

                    target_state = TaskState.working
                    try:
                        target_state = TaskState(status_state)
                    except Exception:
                        pass
                    await updater.update_status(target_state, message)
                    continue
                elif completed:
                    if content:
                        artifact = new_text_artifact(name=artifact_name, text=_safe_text(content))
                        await updater.add_artifact(
                            name=artifact_name,
                            parts=artifact.parts,
                        )
                    await updater.complete()
                    return
                else:
                    if content:
                        artifact = new_text_artifact(name=artifact_name, text=_safe_text(content))
                        await updater.add_artifact(
                            name=artifact_name,
                            parts=artifact.parts,
                        )

            elif isinstance(response, TaskArtifactUpdateEvent):
                if response.artifact and response.artifact.parts:
                    await updater.add_artifact(
                        name="response",
                        parts=_sanitize_parts(response.artifact.parts),
                        artifact_id=str(uuid.uuid4()),
                    )

            elif isinstance(response, TaskStatusUpdateEvent):
                if response.status.state == "failed":
                    error_text = "Remote agent failed"
                    if response.status.message and response.status.message.parts:
                        p = response.status.message.parts[0]
                        if hasattr(p, 'text') and p.text:
                            error_text = p.text
                    message = new_agent_text_message(
                        text=_safe_text(error_text),
                        context_id=context_id,
                        task_id=task_id,
                    )
                    await updater.failed(message)
                    return
                if response.status.message and response.status.message.parts:
                    p = response.status.message.parts[0]
                    if hasattr(p, 'text') and p.text:
                        safe_status_text = _safe_text(p.text)
                        status_message = new_agent_text_message(
                            text=safe_status_text,
                            context_id=context_id,
                            task_id=task_id,
                        )
                        await updater.update_status(
                            TaskState.working,
                            status_message,
                        )

            elif isinstance(response, Message):
                if response.parts:
                    await updater.add_artifact(
                        name="response",
                        parts=_sanitize_parts(response.parts),
                        artifact_id=str(uuid.uuid4()),
                    )

        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')
