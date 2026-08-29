/**
 * A2UI Liquid Renderer (v0.10) for RayRabbit OSS
 * 🐇 Sovereign UI Engine - Zero-dependency
 */

import { LitElement, html, css } from './lit-core.min.js';

// --- Global Design Tokens (Premium Glassmorphism) ---
const theme = css`
    :host {
        --glass: rgba(255, 255, 255, 0.7);
        --glass-border: rgba(255, 255, 255, 0.4);
        --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        --primary: #6366f1;
        --text: #1e293b;
        --text-dim: #64748b;
    }
`;

// --- Core Logic: Model Processor (v0.10) ---
export class ModelProcessor {
    constructor(dataModel = {}) {
        this.dataModel = dataModel;
    }

    resolveValue(value) {
        if (!value) return '';
        if (typeof value === 'object') {
            if (value.path) {
                const resolved = this.getValueByPath(value.path);
                return this.resolveValue(resolved);
            }
            if (value.literalString) return this.resolveValue(value.literalString);
            
            // Si es un objeto de tipo MCP/A2A content envelope, extraer el valor interno
            if (value.content && Array.isArray(value.content) && value.content.length > 0) {
                const first = value.content[0];
                if (first.json !== undefined) return typeof first.json === 'object' ? JSON.stringify(first.json) : String(first.json);
                if (first.text !== undefined) return this.resolveValue(first.text);
            }
            return JSON.stringify(value);
        }

        if (typeof value === 'string' && value.includes('${')) {
            return value.replace(/\$\{([^}]+)\}/g, (_, expression) => {
                const cleanPath = expression.trim();
                const resolved = this.getValueByPath(cleanPath);
                if (resolved !== undefined && resolved !== null) {
                    if (typeof resolved === 'object') {
                        return JSON.stringify(resolved);
                    }
                    return String(resolved);
                }
                return '';
            });
        }

        return value || '';
    }

    getValueByPath(path) {
        if (!path || path === '/') return this.dataModel;
        const parts = path.split('/').filter(p => p);
        let current = this.dataModel;
        for (const part of parts) {
            if (current === null || current[part] === undefined) return undefined;
            current = current[part];
        }
        return current;
    }

    updateDataModel(update) {
        const { path, value } = update;
        if (!path || path === '/') {
            this.dataModel = { ...this.dataModel, ...value };
        } else {
            const parts = path.split('/').filter(p => p);
            let current = this.dataModel;
            for (let i = 0; i < parts.length - 1; i++) {
                if (!current[parts[i]]) current[parts[i]] = {};
                current = current[parts[i]];
            }
            current[parts[parts.length - 1]] = value;
        }
    }
}

// --- Base Component ---
class A2UIComponent extends LitElement {
    static properties = {
        properties: { type: Object },
        processor: { type: Object }
    };
}

// --- Components: Text ---
customElements.define('a2ui-text', class extends A2UIComponent {
    static styles = [theme, css`
        :host { display: block; font-family: 'Outfit', sans-serif; }
        .h1 { font-size: 2rem; font-weight: 700; color: #0f172a; letter-spacing: -0.02em; margin: 0 0 6px 0; }
        .h2 { font-size: 1.35rem; font-weight: 600; color: #1e293b; letter-spacing: -0.01em; margin: 0 0 4px 0; }
        .h3 { font-size: 1.15rem; font-weight: 600; color: #334155; margin: 0 0 4px 0; }
        .body { font-size: 0.95rem; color: #475569; line-height: 1.55; margin: 0; }
        .caption { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; margin: 0; }
        .badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; background: #e0e7ff; color: #3730a3; width: fit-content; }
        .badge-running { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
        .badge-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    `];
    render() {
        const text = this.processor.resolveValue(this.properties.text);
        const usage = this.properties.variant || this.properties.usageHint || 'body';
        return html`<div class="${usage}">${text}</div>`;
    }
});

// --- Components: Image ---
customElements.define('a2ui-image', class extends A2UIComponent {
    static styles = css`
        :host { display: block; overflow: hidden; border-radius: 12px; }
        img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease; }
        .avatar { width: 48px; height: 48px; border-radius: 50%; }
        .feature { height: 200px; }
    `;
    render() {
        const url = this.processor.resolveValue(this.properties.url);
        const variant = this.properties.variant || 'feature';
        return html`<img src="${url}" class="${variant}" alt="${this.properties.description || ''}">`;
    }
});

// --- Components: Card (Premium Design) ---
customElements.define('a2ui-card', class extends A2UIComponent {
    static styles = [theme, css`
        .card {
            display: flex;
            flex-direction: column;
            gap: 12px;
            border-radius: 20px;
            padding: 22px;
            margin: 12px 0;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .glass {
            background: var(--glass);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--glass-shadow);
        }
        .glass:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.6);
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.08);
        }
        .elevated {
            background: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.06);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }
        .flat {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 16px;
            border-radius: 14px;
        }
    `];
    render() {
        const variant = this.properties?.variant || 'glass';
        return html`<div class="card ${variant}"><slot></slot></div>`;
    }
});

// --- Components: ProgressBar (Enterprise Sleek Design) ---
customElements.define('a2ui-progressbar', class extends A2UIComponent {
    static styles = [theme, css`
        :host {
            display: block;
            width: 100%;
            margin: 6px 0;
        }
        .progress-track {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 9999px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
            border-radius: 9999px;
            transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
    `];
    render() {
        let val = this.processor ? this.processor.resolveValue(this.properties?.progress) : 0;
        if (typeof val === 'string') {
            val = parseFloat(val.replace('%', '')) || 0;
        }
        val = Math.min(Math.max(Number(val) || 0, 0), 100);
        return html`
            <div class="progress-track">
                <div class="progress-fill" style="width: ${val}%;"></div>
            </div>
        `;
    }
});

// --- Components: Interactive ---
customElements.define('a2ui-button', class extends A2UIComponent {
    static styles = [theme, css`
        button {
            padding: 12px 24px;
            border-radius: 12px;
            border: none;
            background: var(--primary);
            color: white;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button:hover:not(:disabled) { filter: brightness(1.1); transform: scale(1.02); }
        button:disabled, button.disabled {
            opacity: 0.5;
            cursor: not-allowed;
            filter: grayscale(0.5);
            transform: none !important;
            pointer-events: none;
        }
        .secondary { background: #f1f5f9; color: #475569; }
        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: #ffffff;
            border-radius: 50%;
            animation: a2ui-spin 0.8s linear infinite;
        }
        @keyframes a2ui-spin {
            to { transform: rotate(360deg); }
        }
    `];
    _isDisabled() {
        let dis = this.properties?.disabled;
        if (dis !== undefined && this.processor) {
            dis = this.processor.resolveValue(dis);
        }
        return Boolean(dis === true || dis === 'true');
    }
    _handleClick(e) {
        if (e) e.stopPropagation();
        if (this._isDisabled()) return;
        let action = this.properties?.action;
        let actionId = null;
        if (typeof action === 'string') {
            actionId = action;
        } else if (action && typeof action === 'object') {
            actionId = action.id || action.name || 'action';
        } else {
            actionId = this.properties?.id || (this.id ? this.id.replace(/^comp-/, '') : 'action');
        }
        const detail = { type: 'userAction', id: actionId };
        this.dispatchEvent(new CustomEvent('a2ui-action', {
            detail: detail,
            bubbles: true,
            composed: true
        }));
    }
    render() {
        const variant = this.properties?.variant || 'primary';
        const rawText = this.properties?.label || this.properties?.text;
        const text = this.processor ? this.processor.resolveValue(rawText) : (rawText || '');
        const isDisabled = this._isDisabled();
        return html`
            <button ?disabled="${isDisabled}" @click="${(e) => this._handleClick(e)}" class="${variant} ${isDisabled ? 'disabled' : ''}">
                ${isDisabled ? html`<span class="spinner"></span>` : ''}
                ${text ? text : html`<slot></slot>`}
            </button>
        `;
    }
});

// --- Components: Layouts ---
customElements.define('a2ui-column', class extends A2UIComponent {
    static styles = css`
        .column {
            display: flex;
            flex-direction: column;
            gap: 16px;
            width: 100%;
        }
    `;
    render() {
        const justify = this.properties?.justify || 'start';
        const align = this.properties?.align || 'stretch';
        
        const justifyMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'spaceBetween': 'space-between',
            'space-between': 'space-between'
        };
        const alignMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'stretch': 'stretch'
        };
        
        const jVal = justifyMap[justify] || justify;
        const aVal = alignMap[align] || align;
        
        return html`<div class="column" style="justify-content: ${jVal}; align-items: ${aVal};"><slot></slot></div>`;
    }
});

customElements.define('a2ui-row', class extends A2UIComponent {
    static styles = css`
        .row {
            display: flex;
            flex-direction: row;
            gap: 16px;
            width: 100%;
        }
    `;
    render() {
        const justify = this.properties?.justify || 'start';
        const align = this.properties?.align || 'center';
        
        const justifyMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'spaceBetween': 'space-between',
            'space-between': 'space-between'
        };
        const alignMap = {
            'start': 'flex-start',
            'center': 'center',
            'end': 'flex-end',
            'stretch': 'stretch'
        };
        
        const jVal = justifyMap[justify] || justify;
        const aVal = alignMap[align] || align;
        
        return html`<div class="row" style="justify-content: ${jVal}; align-items: ${aVal};"><slot></slot></div>`;
    }
});

// --- Components: Icon (High-res SVG) ---
customElements.define('a2ui-icon', class extends A2UIComponent {
    static styles = css`
        :host {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            vertical-align: middle;
            color: currentColor;
            width: 24px;
            height: 24px;
        }
        svg {
            width: 100%;
            height: 100%;
            fill: none;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
    `;
    render() {
        const name = (this.properties?.name || '').toLowerCase();
        
        if (name === 'check' || name === 'success') {
            return html`<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        } else if (name === 'info') {
            return html`<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
        } else if (name === 'warning' || name === 'alert') {
            return html`<svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
        } else if (name === 'truck' || name === 'shipping' || name === 'local_shipping') {
            return html`<svg viewBox="0 0 24 24"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>`;
        } else if (name === 'package' || name === 'box') {
            return html`<svg viewBox="0 0 24 24"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>`;
        } else if (name === 'map' || name === 'pin' || name === 'location') {
            return html`<svg viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`;
        } else if (name === 'clock' || name === 'time' || name === 'access_time') {
            return html`<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`;
        } else {
            return html`<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
        }
    }
});

// --- Components: Divider ---
customElements.define('a2ui-divider', class extends A2UIComponent {
    static styles = css`
        .divider {
            border: 0;
            background-color: rgba(0, 0, 0, 0.08);
        }
        .horizontal {
            height: 1px;
            width: 100%;
            margin: 12px 0;
        }
        .vertical {
            width: 1px;
            height: 100%;
            margin: 0 12px;
            display: inline-block;
            align-self: stretch;
        }
    `;
    render() {
        const axis = this.properties?.axis || 'horizontal';
        return html`<hr class="divider ${axis}">`;
    }
});

// --- Main Renderer Registry (v0.10 Native) ---
export class A2UIRenderer {
    constructor(container, processor) {
        this.container = container;
        this.processor = processor;
        this.activeSurfaces = new Map();
        this._pendingUpdates = new Map(); // surfaceId -> { surfaceUpdate, dataModelUpdates: [] }
    }

    render(message) {
        const messages = Array.isArray(message) ? message : [message];
        
        for (const msg of messages) {
            if (msg.beginRendering) {
                this.handleBeginRendering(msg.beginRendering);
            } else if (msg.surfaceUpdate) {
                this.handleSurfaceUpdate(msg.surfaceUpdate);
            } else if (msg.updateDataModel) {
                this.handleUpdateDataModel(msg.updateDataModel);
            } else if (msg.deleteSurface) {
                this.handleDeleteSurface(msg.deleteSurface);
            }
        }
    }

    handleBeginRendering(config) {
        const surfaceId = config.surfaceId;
        console.log(`[A2UI] beginRendering (Signal Received): ${surfaceId}`);
        
        if (surfaceId === "universal_dashboard") {
            const existingSurfaces = this.container.querySelectorAll('.a2ui-surface');
            existingSurfaces.forEach(el => {
                if (el.id !== `surface-${surfaceId}`) {
                    el.remove();
                }
            });
            for (const key of Array.from(this.activeSurfaces.keys())) {
                if (key !== surfaceId) {
                    this.activeSurfaces.delete(key);
                }
            }
        }

        // 1. Asegurar contenedor
        let surface = this.container.querySelector(`#surface-${surfaceId}`);
        if (!surface) {
            surface = document.createElement('div');
            surface.id = `surface-${surfaceId}`;
            surface.className = 'a2ui-surface';
            this.container.appendChild(surface);
        }

        // 2. FLUSH BUFFER: Aplicar actualizaciones acumuladas
        const pending = this._pendingUpdates.get(surfaceId);
        if (pending) {
            // Aplicar estructura
            if (pending.surfaceUpdate) {
                this._applySurfaceUpdate(pending.surfaceUpdate, surface);
            }
            // Aplicar datos
            pending.dataModelUpdates.forEach(update => {
                this.processor.updateDataModel(update);
            });
            // Limpiar buffer
            this._pendingUpdates.delete(surfaceId);
        }

        this.activeSurfaces.set(surfaceId, config);
        this.refresh();
    }

    handleSurfaceUpdate(update) {
        const surfaceId = update.surfaceId;
        if (this.activeSurfaces.has(surfaceId)) {
            console.log(`[A2UI] Active surfaceUpdate for ${surfaceId} - Direct render`);
            let surface = this.container.querySelector(`#surface-${surfaceId}`);
            if (surface) {
                this._applySurfaceUpdate(update, surface);
                this.refresh();
            }
        } else {
            console.log(`[A2UI] Buffering surfaceUpdate for ${surfaceId}`);
            if (!this._pendingUpdates.has(surfaceId)) {
                this._pendingUpdates.set(surfaceId, { surfaceUpdate: null, dataModelUpdates: [] });
            }
            this._pendingUpdates.get(surfaceId).surfaceUpdate = update;
        }
    }

    _applySurfaceUpdate(update, container) {
        container.innerHTML = '';
        const componentsMap = new Map(update.components.map(c => [c.id, c]));
        const rootComponent = componentsMap.get('root') || update.components[0];
        if (rootComponent) {
            this.renderRecursive(rootComponent.id, componentsMap, container);
        }
    }

    handleUpdateDataModel(update) {
        const surfaceId = update.surfaceId;
        if (this.activeSurfaces.has(surfaceId)) {
            console.log(`[A2UI] Active dataModelUpdate for ${surfaceId} - Direct update`);
            this.processor.updateDataModel(update);
            this.refresh();
        } else {
            console.log(`[A2UI] Buffering dataModelUpdate for ${surfaceId}`);
            if (!this._pendingUpdates.has(surfaceId)) {
                this._pendingUpdates.set(surfaceId, { surfaceUpdate: null, dataModelUpdates: [] });
            }
            this._pendingUpdates.get(surfaceId).dataModelUpdates.push(update);
        }
    }

    handleDeleteSurface(update) {
        const surfaceEl = this.container.querySelector(`#surface-${update.surfaceId}`);
        if (surfaceEl) surfaceEl.remove();
        this.activeSurfaces.delete(update.surfaceId);
        this._pendingUpdates.delete(update.surfaceId);
    }

    renderRecursive(id, map, parent) {
        const config = map.get(id);
        if (!config) return;

        const type = Object.keys(config.component)[0];
        const tagName = `a2ui-${type.toLowerCase()}`;

        let el = document.createElement(tagName);
        el.properties = config.component[type];
        el.processor = this.processor;
        el.id = `comp-${id}`;

        // Handle children (v0.10: simple array of IDs)
        const children = el.properties.children || [];
        const childId = el.properties.child;

        if (childId) {
            this.renderRecursive(childId, map, el);
        } else if (Array.isArray(children)) {
            children.forEach(cId => this.renderRecursive(cId, map, el));
        }

        parent.appendChild(el);
    }

    refresh() {
        const elements = this.container.querySelectorAll('*');
        elements.forEach(el => {
            if (el.requestUpdate) el.requestUpdate();
        });
    }
}
