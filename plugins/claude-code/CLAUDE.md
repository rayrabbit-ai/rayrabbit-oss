# RayRabbit Interoperability Directives for Claude Code

You are connected to the **RayRabbit Sovereign Mesh (L3 Interoperability Infrastructure)** via Realtime MCP SSE.

## Core Capabilities & Tools
- **Inter-Agent Messaging**: Use `rayrabbit_send_message` to communicate bidirectionally with other sessions (e.g. `antigravity_core`, `codex_cli_agent`, `crewai_service`, `autogen_service`, `langchain_service`).
- **Distributed Tool Execution**: Invoke sovereign domain tools across nodes using `rayrabbit_call_tool`.
- **L3 Sovereign Memory**: Persist validated facts, architectural decisions, and logistics state across sessions using `rayrabbit_publish_fact`.
- **Mesh Discovery**: Inspect active nodes, framework services, and session status using `rayrabbit_list_agents`.
- **Inbox & Events**: Check pending incoming messages and approvals using `rayrabbit_read_inbox`.

## Zero-Trust Collaboration Rules
1. **Dynamic Discovery**: Never hardcode node endpoints. Dynamically check `rayrabbit_list_agents` when routing.
2. **Correlation ID**: Include a unique `correlation_id` in every task or message to enable end-to-end MAESTRO audit tracking.
3. **Sovereign State**: Respect Shared-Nothing boundaries. Write immutable facts to L3 Memory using `rayrabbit_publish_fact` so other assistants (Antigravity, Codex) can read them.