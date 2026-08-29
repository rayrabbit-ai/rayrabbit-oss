import asyncio
import json
import logging
import inspect
from aiohttp import web
from rayrabbit_client.agents.researcher_agent.researcher_agent import ResearcherAgent

# HTML Template con UI premium al estilo ChatGPT + Consola Multi-Herramientas interactiva y visualmente diseñada
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RayRabbit | Researcher Agent Enterprise</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --primary: #7c3aed;
            --primary-hover: #6d28d9;
            --primary-glow: rgba(124, 58, 237, 0.3);
            --success: #10b981;
            --info: #3b82f6;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg-color: #0b0f19;
            --surface: rgba(17, 24, 39, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --text-muted: #9ca3af;
            --text-default: #d1d5db;
            --text-strong: #ffffff;
            --sidebar-bg: #111827;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0b0f19 70%);
            color: var(--text-default);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1.25rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            font-size: 1.75rem;
        }

        .logo-text {
            color: var(--text-strong);
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        .logo-badge {
            background: var(--primary-glow);
            border: 1px solid var(--primary);
            color: #c084fc;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            text-transform: uppercase;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            color: var(--success);
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--success);
        }

        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            gap: 2rem;
        }

        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.5rem;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 0.75rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .tab-btn:hover {
            color: var(--text-strong);
            background: rgba(255, 255, 255, 0.03);
        }

        .tab-btn.active {
            color: var(--text-strong);
            background: rgba(124, 58, 237, 0.15);
            border: 1px solid rgba(124, 58, 237, 0.3);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease-in-out;
        }

        .tab-content.active {
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }

        /* Tab 1: Chat/Assistant Layout */
        .chat-layout {
            display: grid;
            grid-template-columns: 1.8fr 1fr;
            gap: 2rem;
        }

        @media (max-width: 1024px) {
            .chat-layout {
                grid-template-columns: 1fr;
            }
        }

        .chat-main {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .search-area {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .input-group {
            display: flex;
            gap: 0.75rem;
        }

        .search-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            color: var(--text-strong);
            font-family: inherit;
            font-size: 1rem;
            transition: all 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 8px;
            color: var(--text-strong);
            padding: 0 1.75rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .btn-primary:active {
            transform: translateY(1px);
        }

        /* ChatGPT Style Message */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            min-height: 200px;
        }

        .chat-bubble {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            backdrop-filter: blur(12px);
        }

        .bubble-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .bubble-user {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: var(--text-strong);
        }

        .bubble-body {
            line-height: 1.7;
            font-size: 1.05rem;
        }

        .bubble-body p {
            margin-bottom: 1rem;
        }

        .bubble-body ul, .bubble-body ol {
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }

        .bubble-body li {
            margin-bottom: 0.5rem;
        }

        .bubble-body strong {
            color: var(--text-strong);
        }

        /* Sources Side Panel */
        .sources-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            backdrop-filter: blur(12px);
            height: fit-content;
        }

        .panel-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-strong);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
        }

        .sources-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 0.25rem;
        }

        .source-card {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            transition: all 0.2s;
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .source-card:hover {
            border-color: var(--primary);
            background: rgba(124, 58, 237, 0.05);
            transform: translateY(-2px);
        }

        .source-badge {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            width: fit-content;
            text-transform: uppercase;
        }

        .source-title {
            color: var(--text-strong);
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
        }

        .source-snippet {
            font-size: 0.85rem;
            color: var(--text-muted);
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* Tab 2: Interactive Tool Console */
        .console-layout {
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            gap: 2rem;
        }

        @media (max-width: 1024px) {
            .console-layout {
                grid-template-columns: 1fr;
            }
        }

        .console-left {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            backdrop-filter: blur(12px);
            height: fit-content;
        }

        .console-right {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            backdrop-filter: blur(12px);
            min-height: 500px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-strong);
        }

        .form-select, .form-input, .form-textarea {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.75rem 1rem;
            color: var(--text-strong);
            font-family: inherit;
            font-size: 0.95rem;
            width: 100%;
        }

        .form-select:focus, .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .form-textarea {
            resize: vertical;
            min-height: 120px;
        }

        .output-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-default);
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-strong);
        }

        .json-viewer {
            flex: 1;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            overflow-y: auto;
            max-height: 750px;
            font-size: 1rem;
            line-height: 1.6;
        }

        /* Tab 3: Documentation Layout */
        .docs-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        .docs-section {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .docs-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--text-strong);
            border-left: 4px solid var(--primary);
            padding-left: 0.75rem;
        }

        .code-block-container {
            position: relative;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-top: 0.5rem;
        }

        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border);
            font-family: 'Fira Code', monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .code-content {
            padding: 1.25rem;
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            color: #38bdf8;
            overflow-x: auto;
            white-space: pre;
        }

        /* Utils & Loaders */
        .loader-container {
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            padding: 3rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            backdrop-filter: blur(12px);
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-left-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        .loader-text {
            font-weight: 500;
            color: var(--text-strong);
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            padding: 4rem;
            text-align: center;
            gap: 1rem;
        }

        .empty-icon {
            font-size: 3rem;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.1);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-container">
            <span class="logo-icon">🐰</span>
            <span class="logo-text">RayRabbit</span>
            <span class="logo-badge">Researcher</span>
        </div>
        <div class="status-pill">
            <div class="status-dot"></div>
            <span>Agente Activo (SDK v1.0)</span>
        </div>
    </header>

    <div class="main-container">
        <!-- Tabs Navigation -->
        <div class="tabs-nav">
            <button class="tab-btn active" onclick="switchTab('chat')">🔍 Asistente de Investigación</button>
            <button class="tab-btn" onclick="switchTab('console')">🛠️ Consola de Herramientas</button>
            <button class="tab-btn" onclick="switchTab('docs')">📖 Guía de SDK & CLI</button>
        </div>

        <!-- Tab 1: ChatGPT Assistant -->
        <div id="tab-chat" class="tab-content active">
            <div class="chat-layout">
                <div class="chat-main">
                    <div class="search-area">
                        <div class="input-group">
                            <input type="text" id="chat-query" class="search-input" placeholder="Escribe el tema que deseas investigar hoy (Ej: RayRabbit que es, o avances en baterías de estado sólido)...">
                            <button onclick="executeSearch()" class="btn-primary" id="search-btn">
                                <span>Investigar</span>
                                <span>🚀</span>
                            </button>
                        </div>
                    </div>

                    <!-- Loader -->
                    <div class="loader-container" id="chat-loader">
                        <div class="spinner"></div>
                        <div class="loader-text">DuckDuckGo buscando datos y LiteLLM sintetizando análisis...</div>
                    </div>

                    <!-- Chat Bubble Output -->
                    <div class="chat-container" id="chat-container">
                        <div class="empty-state" id="chat-empty">
                            <div class="empty-icon">🐰</div>
                            <h3>Asistente de Investigación Listo</h3>
                            <p>Escribe tu consulta arriba para buscar en la web y sintetizar información en estilo ChatGPT.</p>
                        </div>
                    </div>
                </div>

                <!-- Sources Side Panel -->
                <div class="sources-panel">
                    <div class="panel-title">
                        <span>📚</span>
                        <span>Fuentes Consultadas</span>
                    </div>
                    <div class="sources-list" id="sources-list">
                        <div style="color: var(--text-muted); text-align: center; padding: 2rem;">
                            Las fuentes web aparecerán aquí una vez finalizada la investigación.
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 2: Interactive Console -->
        <div id="tab-console" class="tab-content">
            <div class="console-layout">
                <div class="console-left">
                    <h2 class="form-label" style="font-size: 1.25rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 0.5rem;">Ejecutor de Herramientas SDK</h2>
                    
                    <div class="form-group">
                        <label class="form-label" for="tool-select">Selecciona la Herramienta a Ejecutar</label>
                        <select id="tool-select" class="form-select" onchange="renderToolInputs()">
                            <option value="web_search">web_search (Búsqueda web con síntesis)</option>
                            <option value="fact_check">fact_check (Verificación de hechos y evidencias)</option>
                            <option value="extract_data">extract_data (Extracción estructurada con Regex)</option>
                            <option value="academic_search">academic_search (Consulta arXiv/PubMed real)</option>
                            <option value="analyze_document">analyze_document (Análisis NLP y VADER de textos)</option>
                            <option value="manage_citations">manage_citations (Formateo de referencias APA/IEEE)</option>
                            <option value="trend_analysis">trend_analysis (Análisis de tendencias temporales)</option>
                            <option value="competitive_intel">competitive_intel (Inteligencia Competitiva de Empresas)</option>
                            <option value="generate_report">generate_report (Generación de Reporte Completo)</option>
                            <option value="get_cache_stats">get_cache_stats (Ver estadísticas de Cache)</option>
                            <option value="clear_cache">clear_cache (Limpiar Cache del Agente)</option>
                        </select>
                    </div>

                    <!-- Contenedor Dinámico de Campos -->
                    <div id="dynamic-inputs" style="display: flex; flex-direction: column; gap: 1.25rem;">
                        <!-- Se poblará vía JavaScript -->
                    </div>

                    <button onclick="executeTool()" class="btn-primary" style="margin-top: 1rem; width: 100%; justify-content: center; padding: 0.85rem 0;" id="console-run-btn">
                        <span>Ejecutar Herramienta</span>
                        <span>🛠️</span>
                    </button>
                </div>

                <div class="console-right">
                    <div class="output-header">
                        <h2 class="form-label" style="font-size: 1.25rem;">Salida del Agente</h2>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <select id="view-mode-toggle" class="form-select" style="padding: 0.35rem 0.75rem; font-size: 0.8rem; width: auto;" onchange="refreshToolOutput()">
                                <option value="styled">Ver Diseñado</option>
                                <option value="json">Ver JSON</option>
                            </select>
                            <button onclick="copyOutput()" class="btn-secondary" style="padding: 0.35rem 0.75rem; font-size: 0.8rem;">Copiar</button>
                        </div>
                    </div>
                    <div class="json-viewer" id="console-output">Esperando ejecución...</div>
                </div>
            </div>
        </div>

        <!-- Tab 3: Documentation -->
        <div id="tab-docs" class="tab-content">
            <div class="docs-container">
                <div class="docs-section">
                    <h2 class="docs-title">¿Cómo usar las demás herramientas del ResearcherAgent?</h2>
                    <p>El agente se encuentra registrado en el Hub de RayRabbit y expone todas sus capacidades como herramientas MCP y A2A. Puedes invocarlas directamente utilizando comandos de consola en Python, la CLI provista, o mediante la API HTTP.</p>
                </div>

                <div class="docs-section">
                    <h3>1. Ejecución vía CLI (Terminal)</h3>
                    <p>Puedes invocar cualquiera de los comandos del agente directamente desde la consola configurando el entorno correspondiente:</p>
                    <div class="code-block-container">
                        <div class="code-header">PowerShell</div>
                        <div class="code-content" id="doc-cli-code"># Ejecutar una extracción de datos estructurada con Regex
$env:PYTHONUTF8=1
$env:PYTHONPATH="clients/python/rayrabbit_client/src"
python -m rayrabbit_client.agents.researcher_agent.cli --query "RayRabbit"</div>
                    </div>
                </div>

                <div class="docs-section">
                    <h3>2. Integración en tu Código Python (SDK)</h3>
                    <p>Puedes instanciar al agente e invocar sus métodos asíncronos programáticamente:</p>
                    <div class="code-block-container">
                        <div class="code-header">Python</div>
                        <div class="code-content">from rayrabbit_client.agents.researcher_agent.researcher_agent import ResearcherAgent
import asyncio

async def main():
    agent = ResearcherAgent(agent_id="mi_investigador")
    
    # 1. Fact-Checking real
    claim = "Python 3.12 es un 30% más rápido que 3.11"
    fact_check_result = await agent._command_fact_check(claim=claim)
    print("Evidencias encontradas:", fact_check_result["supporting_evidence"])

    # 2. Extracción Regex
    texto = "Contáctanos en support@rayrabbit.ai o ventas@example.com"
    extracted = await agent._command_extract_data(content=texto, patterns=["emails"])
    print("Emails detectados:", extracted["extracted_data"]["emails"])

asyncio.run(main())</div>
                    </div>
                </div>

                <div class="docs-section">
                    <h3>3. Formatos y Parámetros de las Herramientas</h3>
                    <p>La siguiente tabla resume las herramientas y los parámetros requeridos que puedes usar tanto en el código como en la **Consola Interactiva (Pestaña 2)**:</p>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 1rem; text-align: left; font-size: 0.95rem;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--border); color: var(--text-strong);">
                                <th style="padding: 0.75rem 1rem;">Herramienta</th>
                                <th style="padding: 0.75rem 1rem;">Parámetros Clave</th>
                                <th style="padding: 0.75rem 1rem;">Descripción</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">fact_check</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">claim: str</td>
                                <td style="padding: 0.75rem 1rem;">Busca evidencias a favor y en contra de una afirmación en internet.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">extract_data</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">content: str, patterns: list</td>
                                <td style="padding: 0.75rem 1rem;">Extrae correos, teléfonos, fechas, valores monetarios y patrones Regex.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">academic_search</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">query: str, databases: list</td>
                                <td style="padding: 0.75rem 1rem;">Busca en bases de datos científicas reales (arXiv y PubMed API).</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">analyze_document</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">content: str, document_type: str</td>
                                <td style="padding: 0.75rem 1rem;">Realiza análisis de sentimientos (VADER) y conteo lingüístico.</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">manage_citations</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">sources: list, citation_style: str</td>
                                <td style="padding: 0.75rem 1rem;">Formatea metadatos a normas académicas (APA, IEEE, MLA, Chicago).</td>
                            </tr>
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.75rem 1rem; font-family: monospace; color: #60a5fa;">trend_analysis</td>
                                <td style="padding: 0.75rem 1rem; font-family: monospace;">topic: str, timeframe: str</td>
                                <td style="padding: 0.75rem 1rem;">Mapea el volumen de búsqueda e inclinación temporal de un tema.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Variables globales para persistir el último estado ejecutado en la consola
        let lastToolExecuted = 'web_search';
        let lastDataReturned = null;

        // Cambiar entre pestañas
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Buscar el botón clicado y activarlo
            const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.textContent.toLowerCase().includes(tabId === 'chat' ? 'asistente' : tabId === 'console' ? 'consola' : 'guía'));
            if (activeBtn) activeBtn.classList.add('active');
            
            document.getElementById(`tab-${tabId}`).classList.add('active');
        }

        // --- LÓGICA DE LA PESTAÑA 1: CHAT AL ESTILO CHATGPT ---
        async function executeSearch() {
            const query = document.getElementById('chat-query').value.trim ? document.getElementById('chat-query').value.trim() : document.getElementById('chat-query').value;
            if (!query) return;
            
            const btn = document.getElementById('search-btn');
            const loader = document.getElementById('chat-loader');
            const container = document.getElementById('chat-container');
            const sourcesList = document.getElementById('sources-list');
            
            // Configurar cargando
            btn.disabled = true;
            loader.style.display = 'flex';
            container.innerHTML = '';
            sourcesList.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 2rem;">Buscando fuentes reales...</div>';
            
            try {
                const res = await fetch('/api/research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await res.json();
                
                // 1. Mostrar respuesta al estilo ChatGPT
                const synthesisHtml = marked.parse(data.synthesis || '*No se recibió síntesis analítica del LLM.*');
                
                container.innerHTML = `
                    <div class="chat-bubble">
                        <div class="bubble-header">
                            <div class="bubble-user">
                                <span>🐰</span>
                                <span>RayRabbit Assistant (gemma-4-31b-it)</span>
                            </div>
                            <span>Investigación Finalizada</span>
                        </div>
                        <div class="bubble-body">
                            ${synthesisHtml}
                        </div>
                    </div>
                `;
                
                // 2. Renderizar Fuentes Consultadas en el panel lateral
                const results = data.results && data.results.results ? data.results.results : [];
                if (results.length > 0) {
                    sourcesList.innerHTML = results.map(src => `
                        <a href="${src.url}" target="_blank" class="source-card">
                            <span class="source-badge">${src.source || 'web'}</span>
                            <div class="source-title">${escapeHtml(src.title)}</div>
                            <div class="source-snippet">${escapeHtml(src.snippet)}</div>
                        </a>
                    `).join('');
                } else {
                    sourcesList.innerHTML = `
                        <div style="color: var(--text-muted); text-align: center; padding: 2rem;">
                            No se recuperaron fuentes clicables para esta consulta.
                        </div>
                    `;
                }
                
            } catch (e) {
                container.innerHTML = `
                    <div class="chat-bubble" style="border-color: var(--danger);">
                        <h3 style="color: var(--danger); margin-bottom: 0.5rem;">❌ Error de Ejecución</h3>
                        <p>${e.message}</p>
                    </div>
                `;
                sourcesList.innerHTML = '<div style="color: var(--danger); text-align: center; padding: 2rem;">Error cargando fuentes.</div>';
            } finally {
                btn.disabled = false;
                loader.style.display = 'none';
            }
        }

        // --- LÓGICA DE LA PESTAÑA 2: CONSOLA MULTI-HERRAMIENTAS ---
        const TOOL_INPUTS_SCHEMA = {
            web_search: [
                { name: 'query', type: 'text', label: 'Término de búsqueda (Query)', placeholder: 'Ej: Avances en IA 2026', required: true },
                { name: 'max_results', type: 'number', label: 'Cantidad máxima de resultados', default: 5 }
            ],
            fact_check: [
                { name: 'claim', type: 'text', label: 'Afirmación a verificar (Claim)', placeholder: 'Ej: El café reduce el riesgo de diabetes tipo 2', required: true }
            ],
            extract_data: [
                { name: 'content', type: 'textarea', label: 'Texto o Contenido', placeholder: 'Escribe o pega el texto aquí...', required: true },
                { name: 'patterns', type: 'text', label: 'Patrones a extraer (separados por comas)', placeholder: 'emails, phones, monetary_values, percentages, urls', required: true }
            ],
            academic_search: [
                { name: 'query', type: 'text', label: 'Término de búsqueda académica', placeholder: 'Ej: neural network transformers', required: true },
                { name: 'databases', type: 'text', label: 'Bases de datos (separadas por comas)', placeholder: 'arxiv, pubmed', default: 'arxiv, pubmed' }
            ],
            analyze_document: [
                { name: 'content', type: 'textarea', label: 'Contenido del documento a analizar', placeholder: 'Pega el texto del documento aquí...', required: true },
                { name: 'document_type', type: 'select', label: 'Tipo de documento', options: ['text', 'pdf', 'docx'], default: 'text' }
            ],
            manage_citations: [
                { name: 'sources', type: 'textarea', label: 'Fuentes (en formato JSON Array)', placeholder: '[{\\n  "title": "Attention Is All You Need",\\n  "authors": ["Vaswani, A."],\\n  "year": "2017"\\n}]', required: true },
                { name: 'citation_style', type: 'select', label: 'Estilo de Cita', options: ['apa', 'ieee', 'mla', 'chicago'], default: 'apa' }
            ],
            trend_analysis: [
                { name: 'topic', type: 'text', label: 'Tema de Tendencias', placeholder: 'Ej: quantum computing adoption', required: true },
                { name: 'timeframe', type: 'select', label: 'Rango de Tiempo', options: ['7d', '30d', '90d', '6months'], default: '30d' }
            ],
            competitive_intel: [
                { name: 'companies', type: 'text', label: 'Compañías a analizar (separadas por comas)', placeholder: 'OpenAI, Anthropic, Google', required: true },
                { name: 'analysis_type', type: 'select', label: 'Tipo de Análisis', options: ['basic', 'swot', 'deep'], default: 'basic' }
            ],
            generate_report: [
                { name: 'topic', type: 'text', label: 'Tema del reporte', placeholder: 'Ej: Energías renovables en Latam', required: true },
                { name: 'format_type', type: 'select', label: 'Formato de Reporte', options: ['markdown', 'html', 'pdf'], default: 'markdown' }
            ],
            get_cache_stats: [],
            clear_cache: []
        };

        function renderToolInputs() {
            const tool = document.getElementById('tool-select').value;
            const container = document.getElementById('dynamic-inputs');
            container.innerHTML = '';
            
            const schema = TOOL_INPUTS_SCHEMA[tool] || [];
            if (schema.length === 0) {
                container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem; padding: 1rem 0;">Esta herramienta no requiere parámetros de entrada adicionales.</div>';
                return;
            }

            schema.forEach(input => {
                const group = document.createElement('div');
                group.className = 'form-group';
                
                const label = document.createElement('label');
                label.className = 'form-label';
                label.textContent = input.label + (input.required ? ' *' : '');
                group.appendChild(label);
                
                if (input.type === 'textarea') {
                    const el = document.createElement('textarea');
                    el.className = 'form-textarea';
                    el.id = `input-${input.name}`;
                    el.placeholder = input.placeholder || '';
                    el.value = input.default || '';
                    group.appendChild(el);
                } else if (input.type === 'select') {
                    const el = document.createElement('select');
                    el.className = 'form-select';
                    el.id = `input-${input.name}`;
                    input.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt;
                        option.textContent = opt.toUpperCase();
                        if (opt === input.default) option.selected = true;
                        el.appendChild(option);
                    });
                    group.appendChild(el);
                } else {
                    const el = document.createElement('input');
                    el.className = 'form-input';
                    el.type = input.type;
                    el.id = `input-${input.name}`;
                    el.placeholder = input.placeholder || '';
                    el.value = input.default || '';
                    group.appendChild(el);
                }
                
                container.appendChild(group);
            });
        }

        async function executeTool() {
            const tool = document.getElementById('tool-select').value;
            const output = document.getElementById('console-output');
            const runBtn = document.getElementById('console-run-btn');
            
            runBtn.disabled = true;
            output.textContent = 'Enviando petición al Agente...';
            output.style.color = '#38bdf8';
            
            // Recopilar argumentos dinámicos
            const schema = TOOL_INPUTS_SCHEMA[tool] || [];
            const arguments = {};
            
            for (const input of schema) {
                const el = document.getElementById(`input-${input.name}`);
                if (!el) continue;
                
                let val = el.value;
                if (input.required && !val) {
                    output.textContent = `Error: El campo "${input.label}" es obligatorio.`;
                    output.style.color = 'var(--danger)';
                    runBtn.disabled = false;
                    return;
                }
                
                // Mapear tipos específicos
                if (input.name === 'patterns' || input.name === 'databases' || input.name === 'companies') {
                    arguments[input.name] = val.split(',').map(s => s.trim()).filter(Boolean);
                } else if (input.name === 'sources') {
                    try {
                        arguments[input.name] = JSON.parse(val);
                    } catch (e) {
                        output.textContent = `Error en campo Fuentes: El formato JSON es inválido. Detalles: ${e.message}`;
                        output.style.color = 'var(--danger)';
                        runBtn.disabled = false;
                        return;
                    }
                } else if (input.type === 'number') {
                    arguments[input.name] = parseInt(val, 10);
                } else {
                    arguments[input.name] = val;
                }
            }
            
            try {
                const res = await fetch('/api/tool', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tool: tool,
                        arguments: arguments
                    })
                });
                const data = await res.json();
                
                lastToolExecuted = tool;
                lastDataReturned = data;
                
                renderToolResult(tool, data);
            } catch (e) {
                output.innerHTML = `
                    <div style="border: 1px solid var(--danger); background: rgba(239, 68, 68, 0.05); padding: 1.5rem; border-radius: 8px; color: var(--danger);">
                        <h3 style="margin-bottom: 0.5rem;">❌ Error de Red</h3>
                        <p>${e.message}</p>
                    </div>
                `;
            } finally {
                runBtn.disabled = false;
            }
        }

        function refreshToolOutput() {
            if (lastDataReturned) {
                renderToolResult(lastToolExecuted, lastDataReturned);
            }
        }

        function renderToolResult(tool, data) {
            const output = document.getElementById('console-output');
            
            if (data.error) {
                output.innerHTML = `
                    <div style="border: 1px solid var(--danger); background: rgba(239, 68, 68, 0.05); padding: 1.5rem; border-radius: 8px; color: var(--danger);">
                        <h3 style="margin-bottom: 0.5rem;">❌ Error de Ejecución</h3>
                        <p>${data.error}</p>
                    </div>
                `;
                return;
            }

            // Verificar modo de vista (JSON vs Diseñado)
            const isJsonMode = document.getElementById('view-mode-toggle').value === 'json';
            if (isJsonMode) {
                output.innerHTML = `<pre style="font-family: 'Fira Code', monospace; color: #a7f3d0; white-space: pre-wrap; overflow: auto; max-height: 700px; font-size: 0.9rem;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
                return;
            }

            // Renderizado diseñado y personalizado para cada herramienta
            let html = '';
            
            if (tool === 'web_search') {
                const synthesisHtml = marked.parse(data.synthesis || '*No se recibió síntesis analítica.*');
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.5rem; border-radius: 8px;">
                            <h3 style="color: var(--text-strong); margin-bottom: 0.75rem; font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">Síntesis de Búsqueda</h3>
                            <div style="line-height: 1.6; font-size: 1rem;">${synthesisHtml}</div>
                        </div>
                        <div>
                            <h4 style="color: var(--text-strong); font-size: 1rem; margin-bottom: 0.75rem;">Fuentes Consultadas (${data.results_count || 0})</h4>
                            <div style="display: grid; grid-template-columns: 1fr; gap: 1rem;">
                                ${(data.results?.results || []).map(src => `
                                    <div style="background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border); padding: 1rem; border-radius: 8px;">
                                        <span class="source-badge">${src.source || 'web'}</span>
                                        <h5 style="color: var(--text-strong); margin: 0.5rem 0 0.25rem 0;"><a href="${src.url}" target="_blank" style="color: #60a5fa; text-decoration: none;">${escapeHtml(src.title)}</a></h5>
                                        <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5;">${escapeHtml(src.snippet)}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            }
            else if (tool === 'fact_check') {
                const status = data.status || 'indeterminado';
                const confidence = data.confidence || 0;
                const statusColors = {
                    verdadero: 'var(--success)',
                    falso: 'var(--danger)',
                    indeterminado: 'var(--warning)',
                    soportado: 'var(--success)',
                    refutado: 'var(--danger)'
                };
                const color = statusColors[status.toLowerCase()] || 'var(--info)';
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.5rem; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;">
                            <div>
                                <h3 style="color: var(--text-strong); font-size: 1.1rem; margin-bottom: 0.25rem;">Veredicto de Verificación</h3>
                                <span style="font-size: 1.5rem; font-weight: 800; color: ${color}; text-transform: uppercase;">${status}</span>
                            </div>
                            <div style="text-align: right; min-width: 150px;">
                                <div style="font-weight: 600; margin-bottom: 0.25rem; font-size: 0.9rem;">Confianza: ${Math.round(confidence * 100)}%</div>
                                <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 9999px; overflow: hidden;">
                                    <div style="width: ${confidence * 100}%; height: 100%; background: ${color};"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                            <div>
                                <h4 style="color: var(--success); font-size: 0.95rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;"><span>✅</span> Evidencias a Favor</h4>
                                <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem;">
                                    ${(data.supporting_evidence || []).length > 0 ? (data.supporting_evidence || []).map(ev => `
                                        <div style="background: rgba(16, 185, 129, 0.02); border: 1px solid rgba(16, 185, 129, 0.12); padding: 1rem; border-radius: 8px; font-size: 0.9rem;">
                                            <p style="margin-bottom: 0.5rem; line-height: 1.5;">${escapeHtml(ev.snippet || ev.text || ev)}</p>
                                            ${ev.url ? `<a href="${ev.url}" target="_blank" style="font-size: 0.8rem; color: #60a5fa; text-decoration: none;">Ver fuente original ↗</a>` : ''}
                                        </div>
                                    `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">Ninguna evidencia concluyente a favor.</p>'}
                                </div>
                            </div>
                            <div>
                                <h4 style="color: var(--danger); font-size: 0.95rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;"><span>❌</span> Evidencias en Contra</h4>
                                <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem;">
                                    ${(data.contradicting_evidence || []).length > 0 ? (data.contradicting_evidence || []).map(ev => `
                                        <div style="background: rgba(239, 68, 68, 0.02); border: 1px solid rgba(239, 68, 68, 0.12); padding: 1rem; border-radius: 8px; font-size: 0.9rem;">
                                            <p style="margin-bottom: 0.5rem; line-height: 1.5;">${escapeHtml(ev.snippet || ev.text || ev)}</p>
                                            ${ev.url ? `<a href="${ev.url}" target="_blank" style="font-size: 0.8rem; color: #60a5fa; text-decoration: none;">Ver fuente original ↗</a>` : ''}
                                        </div>
                                    `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem;">Ninguna evidencia concluyente en contra.</p>'}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            else if (tool === 'extract_data') {
                const extData = data.extracted_data || data;
                const patternKeys = Object.keys(extData).filter(k => Array.isArray(extData[k]));
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.25rem; border-radius: 8px;">
                            <h3 style="color: var(--text-strong); font-size: 1.1rem; margin-bottom: 0.25rem;">Extracción Estructurada Completada</h3>
                            <p style="font-size: 0.85rem; color: var(--text-muted);">Porcentaje de Confianza: ${Math.round((extData.confidence_score || 0) * 100)}%</p>
                        </div>
                        
                        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                            ${patternKeys.map(key => {
                                const list = extData[key];
                                if (list.length === 0) return '';
                                return `
                                    <div>
                                        <h4 style="color: var(--text-strong); text-transform: uppercase; font-size: 0.85rem; margin-bottom: 0.5rem; letter-spacing: 0.5px;">${key.replace('_', ' ')} (${list.length})</h4>
                                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                            ${list.map(item => {
                                                const val = typeof item === 'object' ? item.value : item;
                                                const conf = typeof item === 'object' && item.confidence ? ` (${Math.round(item.confidence*100)}%)` : '';
                                                return `
                                                    <span style="background: rgba(124, 58, 237, 0.1); border: 1px solid rgba(124, 58, 237, 0.25); color: #c084fc; padding: 0.4rem 0.75rem; border-radius: 6px; font-size: 0.85rem; font-family: 'Fira Code', monospace;">
                                                        ${escapeHtml(val)}${conf}
                                                    </span>
                                                `;
                                            }).join('')}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                            ${patternKeys.every(k => extData[k].length === 0) ? '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No se encontraron coincidencias para los patrones especificados en el texto.</p>' : ''}
                        </div>
                    </div>
                `;
            }
            else if (tool === 'academic_search') {
                const academicResults = data.results || {};
                const databases = Object.keys(academicResults);
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        ${databases.map(db => {
                            const papers = academicResults[db] || [];
                            return `
                                <div>
                                    <h3 style="color: var(--text-strong); text-transform: uppercase; font-size: 0.95rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between;">
                                        <span>🔍 Base de datos: ${db}</span>
                                        <span style="color: var(--text-muted); font-size: 0.8rem;">${papers.length} artículos</span>
                                    </h3>
                                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                                        ${papers.length > 0 ? papers.map(paper => `
                                            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.25rem; border-radius: 8px;">
                                                <h4 style="color: var(--text-strong); font-size: 1rem; margin-bottom: 0.5rem;">
                                                    ${paper.url ? `<a href="${paper.url}" target="_blank" style="color: #60a5fa; text-decoration: none;">${escapeHtml(paper.title)}</a>` : escapeHtml(paper.title)}
                                                </h4>
                                                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                                                    <strong>Autores:</strong> ${(paper.authors || []).join(', ') || 'Desconocido'} | <strong>Año:</strong> ${paper.year || 'N/A'}
                                                </p>
                                                ${paper.summary || paper.abstract ? `<p style="font-size: 0.9rem; line-height: 1.5; color: var(--text-default);">${escapeHtml(paper.summary || paper.abstract)}</p>` : ''}
                                            </div>
                                        `).join('') : '<p style="color: var(--text-muted); font-size: 0.85rem; padding: 0.5rem 0;">No se encontraron artículos académicos en esta base de datos.</p>'}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            else if (tool === 'analyze_document') {
                const analysis = data.analysis || data;
                const sentiment = analysis.sentiment || {};
                const comp = sentiment.compound !== undefined ? sentiment.compound : 0;
                let sentimentLabel = 'Neutral 😐';
                let sentimentColor = 'var(--info)';
                if (comp > 0.1) { sentimentLabel = 'Positivo 🙂'; sentimentColor = 'var(--success)'; }
                else if (comp < -0.1) { sentimentLabel = 'Negativo 🙁'; sentimentColor = 'var(--danger)'; }
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Palabras</div>
                                <div style="font-size: 1.75rem; font-weight: 800; color: var(--text-strong); margin-top: 0.25rem;">${analysis.word_count || 0}</div>
                            </div>
                            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Oraciones</div>
                                <div style="font-size: 1.75rem; font-weight: 800; color: var(--text-strong); margin-top: 0.25rem;">${analysis.sentence_count || 0}</div>
                            </div>
                            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; text-align: center;">
                                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Sentimiento</div>
                                <div style="font-size: 1.25rem; font-weight: 800; color: ${sentimentColor}; margin-top: 0.5rem;">${sentimentLabel}</div>
                            </div>
                        </div>
                        
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.25rem; border-radius: 8px; display: flex; align-items: center; gap: 1rem; justify-content: space-between; flex-wrap: wrap;">
                            <span style="font-weight: 600; font-size: 0.95rem;">Distribución de Sentimiento VADER (Compound: ${comp}):</span>
                            <div style="flex: 1; min-width: 200px; max-width: 300px; height: 10px; background: rgba(255,255,255,0.1); border-radius: 9999px; overflow: hidden; position: relative;">
                                <div style="position: absolute; left: 50%; width: 2px; height: 100%; background: white; z-index: 2;"></div>
                                <div style="position: absolute; ${comp >= 0 ? `left: 50%; width: ${comp * 50}%; background: var(--success);` : `right: 50%; width: ${Math.abs(comp) * 50}%; background: var(--danger);`} height: 100%;"></div>
                            </div>
                        </div>
                        
                        <div>
                            <h4 style="color: var(--text-strong); font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Palabras Clave Principales (Keywords)</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                ${(analysis.top_keywords || []).map(kw => `
                                    <span style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 0.35rem 0.65rem; border-radius: 6px; font-size: 0.85rem;">
                                        ${escapeHtml(kw)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            }
            else if (tool === 'manage_citations') {
                const list = data.citations || [];
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <h3 style="color: var(--text-strong); font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">Referencias Académicas Formateadas (${data.citation_style?.toUpperCase() || 'APA'})</h3>
                        <div style="display: flex; flex-direction: column; gap: 1rem;">
                            ${list.map((cit, idx) => `
                                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
                                    <div style="font-family: serif; font-size: 1.05rem; line-height: 1.5; color: var(--text-strong);">
                                        ${escapeHtml(cit.formatted)}
                                    </div>
                                    <button onclick="navigator.clipboard.writeText('${cit.formatted.replace(/'/g, "\\'")}')" class="btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem; white-space: nowrap;">Copiar Cita</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            else if (tool === 'trend_analysis') {
                const trends = data.trends || data;
                const points = trends.data_points || [];
                const dir = trends.trend_direction || 'neutral';
                const dirColors = { increasing: 'var(--success)', decreasing: 'var(--danger)', neutral: 'var(--info)' };
                const dirSymbols = { increasing: '📈 ALZA', decreasing: '📉 BAJA', neutral: '➡️ ESTABLE' };
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 1.5rem; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                            <div>
                                <h3 style="color: var(--text-strong); margin-bottom: 0.25rem; font-size: 1rem;">Dirección de Tendencia</h3>
                                <span style="font-size: 1.5rem; font-weight: 800; color: ${dirColors[dir]};">${dirSymbols[dir] || dir.toUpperCase()}</span>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.8rem; color: var(--text-muted);">Puntuación de Tendencia</div>
                                <div style="font-size: 1.75rem; font-weight: 800; color: var(--text-strong);">${trends.trend_score || 0}</div>
                            </div>
                        </div>
                        
                        <div>
                            <h4 style="color: var(--text-strong); font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase;">Puntos Temporales Ordenados</h4>
                            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                ${points.map(p => `
                                    <div style="background: rgba(0,0,0,0.2); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-family: 'Fira Code', monospace; font-size: 0.85rem; flex-wrap: wrap; gap: 0.5rem;">
                                        <span style="color: var(--text-muted);">${p.date || p.published_date}</span>
                                        <span style="font-weight: 600; color: var(--text-strong);">${p.title || p.topic || 'Punto de datos'}</span>
                                        <span style="color: ${p.sentiment?.compound >= 0.1 ? 'var(--success)' : p.sentiment?.compound <= -0.1 ? 'var(--danger)' : 'var(--text-default)'}">
                                            Comp: ${p.sentiment?.compound?.toFixed(2) || '0.00'}
                                        </span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            }
            else if (tool === 'competitive_intel') {
                const analysis = data.analysis || {};
                const companies = Object.keys(analysis);
                
                html = `
                    <div style="display: flex; flex-direction: column; gap: 2rem;">
                        ${companies.map(company => {
                            const compData = analysis[company] || {};
                            const swot = compData.swot_analysis || {};
                            const market = compData.market_analysis || {};
                            
                            return `
                                <div style="background: rgba(255, 255, 255, 0.01); border: 1px solid var(--border); padding: 1.5rem; border-radius: 12px; display: flex; flex-direction: column; gap: 1.25rem;">
                                    <h3 style="color: var(--text-strong); font-size: 1.3rem; border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                                        <span>🏢 Competidor: ${company.toUpperCase()}</span>
                                        <span style="background: var(--primary-glow); border: 1px solid var(--primary); font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 6px; color: #c084fc; font-weight: 600;">Inteligencia Competitiva</span>
                                    </h3>
                                    
                                    <!-- Información del Mercado -->
                                    <div style="background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border); padding: 1rem; border-radius: 8px; font-size: 0.9rem; line-height: 1.6;">
                                        <strong>Tamaño del mercado:</strong> ${market.market_size || 'N/A'} | 
                                        <strong>Tendencia de Crecimiento:</strong> ${market.growth_trend || 'N/A'} | 
                                        <strong>Entorno Regulatorio:</strong> ${market.regulatory_environment || 'N/A'}<br>
                                        <strong>Segmento de Mercado:</strong> ${escapeHtml(market.market_segment || 'N/A')}
                                    </div>
                                    
                                    <!-- SWOT Analysis Grid -->
                                    <div>
                                        <h4 style="color: var(--text-strong); font-size: 0.85rem; margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">Matriz DAFO / SWOT</h4>
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                            <!-- Fortalezas -->
                                            <div style="background: rgba(16, 185, 129, 0.02); border: 1px solid rgba(16, 185, 129, 0.15); padding: 1rem; border-radius: 8px;">
                                                <h5 style="color: var(--success); font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.25rem; font-size: 0.9rem;">💪 Fortalezas</h5>
                                                <ul style="margin-left: 1.25rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-default); display: flex; flex-direction: column; gap: 0.25rem;">
                                                    ${(swot.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('') || '<li>No se detectaron fortalezas críticas en la web.</li>'}
                                                </ul>
                                            </div>
                                            
                                            <!-- Debilidades -->
                                            <div style="background: rgba(239, 68, 68, 0.02); border: 1px solid rgba(239, 68, 68, 0.15); padding: 1rem; border-radius: 8px;">
                                                <h5 style="color: var(--danger); font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.25rem; font-size: 0.9rem;">⚠️ Debilidades</h5>
                                                <ul style="margin-left: 1.25rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-default); display: flex; flex-direction: column; gap: 0.25rem;">
                                                    ${(swot.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('') || '<li>No se detectaron debilidades críticas en la web.</li>'}
                                                </ul>
                                            </div>
                                            
                                            <!-- Oportunidades -->
                                            <div style="background: rgba(59, 130, 246, 0.02); border: 1px solid rgba(59, 130, 246, 0.15); padding: 1rem; border-radius: 8px;">
                                                <h5 style="color: var(--info); font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.25rem; font-size: 0.9rem;">🚀 Oportunidades</h5>
                                                <ul style="margin-left: 1.25rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-default); display: flex; flex-direction: column; gap: 0.25rem;">
                                                    ${(swot.opportunities || []).map(o => `<li>${escapeHtml(o)}</li>`).join('') || '<li>No se detectaron oportunidades comerciales.</li>'}
                                                </ul>
                                            </div>
                                            
                                            <!-- Amenazas -->
                                            <div style="background: rgba(245, 158, 11, 0.02); border: 1px solid rgba(245, 158, 11, 0.15); padding: 1rem; border-radius: 8px;">
                                                <h5 style="color: var(--warning); font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.25rem; font-size: 0.9rem;">🔥 Amenazas</h5>
                                                <ul style="margin-left: 1.25rem; font-size: 0.85rem; line-height: 1.5; color: var(--text-default); display: flex; flex-direction: column; gap: 0.25rem;">
                                                    ${(swot.threats || []).map(t => `<li>${escapeHtml(t)}</li>`).join('') || '<li>No se detectaron amenazas competitivas.</li>'}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Recomendaciones -->
                                    <div>
                                        <h4 style="color: var(--text-strong); font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">Recomendaciones Estratégicas</h4>
                                        <ul style="margin-left: 1.5rem; font-size: 0.9rem; line-height: 1.6; display: flex; flex-direction: column; gap: 0.35rem;">
                                            ${(compData.recommendations || []).map(rec => `<li>${escapeHtml(rec)}</li>`).join('') || '<li>Monitorear el desempeño global del competidor periódicamente.</li>'}
                                        </ul>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }
            else if (tool === 'generate_report') {
                const reportHtml = marked.parse(data.report || '*No se generó reporte de investigación.*');
                html = `
                    <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); padding: 2rem; border-radius: 8px; line-height: 1.7; font-size: 1.05rem;">
                        ${reportHtml}
                    </div>
                `;
            }
            else {
                // Fallback para get_cache_stats, clear_cache o retornos informacionales simples
                html = `
                    <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid var(--success); padding: 1.5rem; border-radius: 8px;">
                        <h3 style="color: var(--success); font-size: 1.1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem;"><span>✅</span> Ejecución Exitosa</h3>
                        <p style="margin-bottom: 1rem; color: var(--text-default); font-weight: 500;">${data.message || 'La herramienta se ejecutó correctamente.'}</p>
                        <pre style="font-family: 'Fira Code', monospace; font-size: 0.85rem; color: #a7f3d0; background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 6px; overflow: auto; max-height: 200px;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
                    </div>
                `;
            }

            output.innerHTML = html;
            output.style.color = 'var(--text-default)';
        }

        // Helpers
        function escapeHtml(unsafe) {
            if (!unsafe) return '';
            return unsafe
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }

        // Inicialización
        renderToolInputs();
    </script>
</body>
</html>
"""

class WebDashboard:
    def __init__(self, agent: ResearcherAgent):
        self.agent = agent
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_post('/api/research', self.handle_research)
        self.app.router.add_post('/api/tool', self.handle_tool_execution)

        # Mapear los nombres de herramientas registrados en el SDK con sus funciones de comando correspondientes
        self.tool_map = {
            "web_search": self.agent._command_web_search,
            "analyze_document": self.agent._command_analyze_document,
            "fact_check": self.agent._command_fact_check,
            "generate_report": self.agent._command_generate_report,
            "extract_data": self.agent._command_extract_data,
            "trend_analysis": self.agent._command_trend_analysis,
            "academic_search": self.agent._command_academic_search,
            "manage_citations": self.agent._command_manage_citations,
            "competitive_intel": self.agent._command_competitive_intelligence,
            "clear_cache": self.agent._command_clear_cache,
            "get_cache_stats": self.agent._command_get_cache_stats,
        }

    async def handle_index(self, request):
        return web.Response(text=HTML_CONTENT, content_type='text/html')

    async def handle_research(self, request):
        data = await request.json()
        query = data.get("query")
        if not query:
            return web.json_response({"error": "No query provided"}, status=400)
            
        try:
            # Ejecuta la herramienta de búsqueda del agente
            result = await self.agent._command_web_search(query=query)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def handle_tool_execution(self, request):
        data = await request.json()
        tool_name = data.get("tool")
        arguments = data.get("arguments", {})
        
        if not tool_name or tool_name not in self.tool_map:
            return web.json_response({"error": f"Tool '{tool_name}' not found or not registered"}, status=400)
            
        try:
            method = self.tool_map[tool_name]
            # Verificar si es una corrutina (async) o función tradicional
            if inspect.iscoroutinefunction(method):
                result = await method(**arguments)
            else:
                result = method(**arguments)
            return web.json_response(result)
        except Exception as e:
            logging.getLogger("RayRabbitSDK-Web").error(f"Error ejecutando {tool_name}: {e}")
            return web.json_response({"error": str(e)}, status=500)

async def start_server():
    agent = ResearcherAgent(agent_id="web_researcher")
    
    # Iniciar conexión al hub en background
    asyncio.create_task(agent.connect())
    
    dashboard = WebDashboard(agent)
    runner = web.AppRunner(dashboard.app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    print("🌐 Web Dashboard del ResearcherAgent ejecutándose en http://localhost:8080")
    
    # Mantener vivo
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\nServidor detenido.")
