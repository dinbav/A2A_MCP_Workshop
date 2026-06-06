from a2a.server.agent_execution import AgentExecutor as _AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart


def _make_part(text: str) -> Part:
    return Part(root=TextPart(text=str(text)))


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
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        history = context.current_task.history if context.current_task else []
        async for response in self.agent.stream(context.get_user_input(), history=history):
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

        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')
