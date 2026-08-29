import pathlib

def build_claude_plugin():
    base = pathlib.Path('plugins/claude-code')
    base.mkdir(parents=True, exist_ok=True)
    (base / 'commands').mkdir(parents=True, exist_ok=True)

    mcp_json = """{
  "mcpServers": {
    "rayrabbit_mesh": {
      "url": "http://127.0.0.1:8005/api/mcp/sse",
      "transport": "sse",
      "headers": {
        "X-RayRabbit-Agent-ID": "claude_code_agent"
      }
    }
  }
}"""
    (base / '.mcp.json').write_text(mcp_json.strip(), encoding='utf-8')
    (base / 'claude_desktop_config.json').write_text(mcp_json.strip(), encoding='utf-8')

    claude_md = """# 🐰 RayRabbit Interoperability Directives for Claude Code

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
"""
    (base / 'CLAUDE.md').write_text(claude_md.strip(), encoding='utf-8')

    mesh_cmd = """---
description: Query the status and topology of the RayRabbit sovereign mesh
---

1. Call `rayrabbit_list_agents` to inspect online nodes.
2. Call `rayrabbit_get_telemetry` to check cluster health and message latency.
3. Display a clean markdown table with Agent IDs, Roles, Ports, and Health status.
"""
    (base / 'commands' / 'mesh.md').write_text(mesh_cmd.strip(), encoding='utf-8')

    readme_md = """# 🐰 RayRabbit Plugin for Anthropic Claude Code & Claude Desktop

Official plugin connecting Claude Code to the **RayRabbit Sovereign Mesh L3 (AI TCP/IP + TLS + HTTP)** via **Realtime MCP Server-Sent Events (SSE)**.

## Quick Installation

### Option A: Claude Code CLI
```bash
claude mcp add rayrabbit http://127.0.0.1:8005/api/mcp/sse
```

### Option B: Claude Desktop Configuration
Copy `claude_desktop_config.json` into your Claude Desktop configuration directory:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\\Claude\\claude_desktop_config.json`

## Features
- ⚡ **Realtime Streaming (<10ms)**: Zero polling via Server-Sent Events.
- 🛡️ **MAESTRO Zero-Trust**: Inter-agent authentication and immutable audit logs.
- 🤝 **Trilateral Interoperability**: Seamlessly collaborate with Google Antigravity and OpenAI Codex sessions.
"""
    (base / 'README.md').write_text(readme_md.strip(), encoding='utf-8')
    print('Claude Code plugin files generated.')


def build_codex_plugin():
    base = pathlib.Path('plugins/codex')
    base.mkdir(parents=True, exist_ok=True)
    (base / '.cursor').mkdir(parents=True, exist_ok=True)

    cursor_mcp = """{
  "mcpServers": {
    "rayrabbit_mesh": {
      "url": "http://127.0.0.1:8005/api/mcp/sse",
      "transport": "sse",
      "headers": {
        "X-RayRabbit-Agent-ID": "codex_cli_agent"
      }
    }
  }
}"""
    (base / '.cursor' / 'mcp.json').write_text(cursor_mcp.strip(), encoding='utf-8')
    (base / 'codex_config.json').write_text(cursor_mcp.strip(), encoding='utf-8')

    cursorrules = """# 🐰 RayRabbit Interoperability Rules for OpenAI Codex & Cursor

You are connected to the **RayRabbit Sovereign Mesh L3** (AI TCP/IP + TLS + HTTP).

## Collaboration Guidelines
1. You can delegate long-running analysis, UI tasks, or framework jobs to other assistants in the mesh using `rayrabbit_send_message` (e.g. to `antigravity_core` for UI/frontend or `claude_code_agent` for deep refactoring).
2. Query the live tool catalog using `rayrabbit_call_tool` to execute logistics, SAP TM, crypto, and database tools.
3. Keep track of tasks via `rayrabbit_publish_fact` to persist verifiable milestones in the L3 Sovereign Memory database.
4. Check for incoming messages and task responses using `rayrabbit_read_inbox`.
"""
    (base / '.cursorrules').write_text(cursorrules.strip(), encoding='utf-8')
    (base / 'CODEX.md').write_text(cursorrules.strip(), encoding='utf-8')

    readme_md = """# 🐰 RayRabbit Plugin for OpenAI Codex, Cursor & OpenAI CLI

Official plugin connecting OpenAI Codex, Cursor IDE, and CLI agents to the **RayRabbit Sovereign Mesh L3 (AI TCP/IP + TLS + HTTP)** via **Realtime MCP Server-Sent Events (SSE)**.

## Quick Installation

### Option A: Cursor IDE
Copy `.cursor/mcp.json` to your project's `.cursor/mcp.json` or add it to Cursor Settings -> MCP.

### Option B: OpenAI Codex / Custom Agent
Import `codex_config.json` in your agent startup configuration.

## Features
- ⚡ **Realtime MCP SSE**: Instant connection to Hub `:8005/api/mcp/sse`.
- 🤝 **Trilateral Peer Connection**: Talk to Antigravity and Claude Code sessions across the local mesh or remote VPCs.
"""
    (base / 'README.md').write_text(readme_md.strip(), encoding='utf-8')
    print('Codex plugin files generated.')


if __name__ == '__main__':
    build_claude_plugin()
    build_codex_plugin()
