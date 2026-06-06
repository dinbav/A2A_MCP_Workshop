from a2a.server.agent_execution import AgentExecutor as _AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils.artifact import new_text_artifact
from a2a.utils.message import new_agent_text_message


class BaseAgentExecutor(_AgentExecutor):
    """
    Shared executor for agents whose logic yields structured dicts:
      {"completed": bool, "failed": bool, "input_required": bool, "content": str}
    """

    def _make_logic(self):
        raise NotImplementedError

    def __init__(self):
        self.agent = self._make_logic()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id
        updater = TaskUpdater(event_queue, task_id, context_id)

        def _safe_text(value: str) -> str:
            # Guard against lone surrogate characters that break UTF-8 serialization.
            return str(value).encode("utf-8", errors="replace").decode("utf-8", errors="replace")

        history = context.current_task.history if context.current_task else []
        async for response in self.agent.stream(context.get_user_input(), history=history):
            completed      = response.get("completed", False)
            failed         = response.get("failed", False)
            input_required = response.get("input_required", False)
            content        = response.get("content", "")
            safe_content = _safe_text(content)

            if failed:
                message = new_agent_text_message(text=safe_content, context_id=context_id, task_id=task_id)
                await updater.failed(message)
                return
            elif input_required:
                message = new_agent_text_message(text=safe_content, context_id=context_id, task_id=task_id)
                await updater.requires_input(message)
            elif completed:
                if content:
                    artifact = new_text_artifact(name="response", text=safe_content)
                    await updater.add_artifact(
                        name="response",
                        parts=artifact.parts,
                    )
                await updater.complete()
                return
            else:
                if content:
                    artifact = new_text_artifact(name="response", text=safe_content)
                    await updater.add_artifact(
                        name="response",
                        parts=artifact.parts,
                    )

        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')
