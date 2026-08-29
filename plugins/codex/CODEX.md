# RayRabbit Interoperability Rules for OpenAI Codex & Cursor

You are connected to the **RayRabbit Sovereign Mesh L3** (AI TCP/IP + TLS + HTTP).

## Collaboration Guidelines
1. You can delegate long-running analysis, UI tasks, or framework jobs to other assistants in the mesh using `rayrabbit_send_message` (e.g. to `antigravity_core` for UI/frontend or `claude_code_agent` for deep refactoring).
2. Query the live tool catalog using `rayrabbit_call_tool` to execute logistics, SAP TM, crypto, and database tools.
3. Keep track of tasks via `rayrabbit_publish_fact` to persist verifiable milestones in the L3 Sovereign Memory database.
4. Check for incoming messages and task responses using `rayrabbit_read_inbox`.