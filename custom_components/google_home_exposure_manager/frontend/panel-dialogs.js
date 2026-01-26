/**
 * Dialog renderers for Google Home Exposure Manager Panel
 * Contains preview, unsaved changes, and entity config dialogs.
 */

import { html } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

/**
 * Render a single config change item.
 */
function renderConfigChange(change) {
  if (change.field === "name") {
    return html`
      <span class="change-item">
        <strong>Name:</strong>
        ${change.old ? html`<span class="change-old">${change.old}</span> →` : ''}
        ${change.new ? html`<span class="change-new">${change.new}</span>` : html`<em>(removed)</em>`}
      </span>
    `;
  }
  if (change.field === "aliases") {
    return html`
      <span class="change-item">
        <strong>Aliases:</strong>
        ${change.added?.length > 0 ? html`<span class="change-new">+${change.added.join(", ")}</span>` : ''}
        ${change.removed?.length > 0 ? html`<span class="change-old">-${change.removed.join(", ")}</span>` : ''}
      </span>
    `;
  }
  if (change.field === "room") {
    return html`
      <span class="change-item">
        <strong>Room:</strong>
        ${change.old ? html`<span class="change-old">${change.old}</span> →` : ''}
        ${change.new ? html`<span class="change-new">${change.new}</span>` : html`<em>(removed)</em>`}
      </span>
    `;
  }
  return '';
}

/**
 * Render the preview dialog showing exposure statistics.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The dialog template
 */
export function renderPreviewDialog(context) {
  const preview = context._preview || {};
  const reasons = preview.exclusion_reasons || {};
  const exposedWithConfig = preview.exposed_with_config || [];
  const configChanges = preview.config_changes || [];

  // Count entities with custom config
  const withAliases = exposedWithConfig.filter(e => e.aliases?.length > 0).length;
  const withNames = exposedWithConfig.filter(e => e.name).length;
  const withRooms = exposedWithConfig.filter(e => e.room).length;

  return html`
    <div class="preview-overlay" @click=${(e) => {
      if (e.target === e.currentTarget) context._showPreview = false;
    }}>
      <div class="preview-dialog">
        <h2>Preview Changes</h2>

        <div class="preview-stats">
          <div class="stat-card exposed">
            <div class="stat-number">${preview.exposed?.length || 0}</div>
            <div class="stat-label">Exposed</div>
          </div>
          <div class="stat-card excluded">
            <div class="stat-number">${preview.excluded?.length || 0}</div>
            <div class="stat-label">Excluded</div>
          </div>
          <div class="stat-card unset">
            <div class="stat-number">${preview.unset?.length || 0}</div>
            <div class="stat-label">Unset</div>
          </div>
        </div>

        ${configChanges.length > 0 ? html`
          <div class="changes-section">
            <div class="changes-title">📝 Configuration Changes (${configChanges.length})</div>
            <div class="changes-list">
              ${configChanges.map(item => html`
                <div class="change-entity">
                  <span class="change-entity-id">${item.entity_id}</span>
                  <div class="change-details">
                    ${item.changes.map(c => renderConfigChange(c))}
                  </div>
                </div>
              `)}
            </div>
          </div>
        ` : ''}

        ${preview.exposed?.length > 0 ? html`
          <details class="preview-section" open>
            <summary>
              ✅ Exposed Entities (${preview.exposed.length})
              ${withAliases > 0 || withNames > 0 || withRooms > 0 ? html`
                <span class="config-summary">
                  ${withNames > 0 ? html`<span class="preview-badge">📛 ${withNames}</span>` : ''}
                  ${withAliases > 0 ? html`<span class="preview-badge">🏷️ ${withAliases}</span>` : ''}
                  ${withRooms > 0 ? html`<span class="preview-badge">📍 ${withRooms}</span>` : ''}
                </span>
              ` : ''}
            </summary>
            <div class="preview-list exposed-list">
              ${exposedWithConfig.map(e => html`
                <div class="exposed-entity ${e.aliases?.length || e.name || e.room ? 'has-config' : ''}">
                  <span class="entity-id">${e.entity_id}</span>
                  ${e.name ? html`<span class="entity-detail">📛 ${e.name}</span>` : ''}
                  ${e.aliases?.length > 0 ? html`
                    <span class="entity-detail">🏷️ ${e.aliases.join(", ")}</span>
                  ` : ''}
                  ${e.room ? html`<span class="entity-detail">📍 ${e.room}</span>` : ''}
                </div>
              `)}
            </div>
          </details>
        ` : ""}

        ${preview.excluded?.length > 0 ? html`
          <div class="exclusion-breakdown">
            <div class="breakdown-title">Exclusion Breakdown:</div>
            <div class="breakdown-items">
              ${reasons.entity_override?.length > 0 ? html`
                <span class="breakdown-item">🚫 Entity overrides: ${reasons.entity_override.length}</span>
              ` : ''}
              ${reasons.device_override?.length > 0 ? html`
                <span class="breakdown-item">📱 Device overrides: ${reasons.device_override.length}</span>
              ` : ''}
              ${reasons.area?.length > 0 ? html`
                <span class="breakdown-item">📍 Area exclusions: ${reasons.area.length}</span>
              ` : ''}
              ${reasons.pattern?.length > 0 ? html`
                <span class="breakdown-item">🔍 Pattern exclusions: ${reasons.pattern.length}</span>
              ` : ''}
            </div>
          </div>

          ${reasons.area?.length > 0 ? html`
            <details class="preview-section">
              <summary>📍 Excluded by Area (${reasons.area.length})</summary>
              <div class="preview-list">
                ${reasons.area.map(e => html`<div>${e}</div>`)}
              </div>
            </details>
          ` : ""}

          ${reasons.pattern?.length > 0 ? html`
            <details class="preview-section">
              <summary>🔍 Excluded by Pattern (${reasons.pattern.length})</summary>
              <div class="preview-list">
                ${reasons.pattern.map(e => html`<div>${e}</div>`)}
              </div>
            </details>
          ` : ""}

          ${(reasons.entity_override?.length > 0 || reasons.device_override?.length > 0) ? html`
            <details class="preview-section">
              <summary>🚫 Excluded by Override (${(reasons.entity_override?.length || 0) + (reasons.device_override?.length || 0)})</summary>
              <div class="preview-list">
                ${(reasons.entity_override || []).map(e => html`<div>${e} <span style="color: var(--secondary-text-color)">(entity)</span></div>`)}
                ${(reasons.device_override || []).map(e => html`<div>${e} <span style="color: var(--secondary-text-color)">(device)</span></div>`)}
              </div>
            </details>
          ` : ""}
        ` : ''}

        <div class="sync-notice">
          After saving, say "Hey Google, sync my devices" to update Google Home.
        </div>

        <div class="action-buttons">
          <button class="btn btn-secondary" @click=${() => context._showPreview = false}>
            Cancel
          </button>
          <button
            class="btn btn-primary"
            @click=${() => context._saveConfig()}
            ?disabled=${context._saving}
          >
            ${context._saving ? "Saving..." : "Save Configuration"}
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render the unsaved changes confirmation dialog.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The dialog template
 */
export function renderUnsavedDialog(context) {
  return html`
    <div class="preview-overlay" @click=${(e) => {
      if (e.target === e.currentTarget) context._cancelNavigation();
    }}>
      <div class="unsaved-dialog">
        <h2>⚠️ Unsaved Changes</h2>
        <p>
          You have unsaved changes. Would you like to save them before continuing?
        </p>
        <div class="action-buttons">
          <button class="btn btn-danger" @click=${() => context._confirmNavigation()}>
            Discard Changes
          </button>
          <button class="btn btn-secondary" @click=${() => context._cancelNavigation()}>
            Stay Here
          </button>
          <button class="btn btn-primary" @click=${() => context._saveAndNavigate()}>
            Preview & Save
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render alias suggestions for the entity config dialog.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The suggestions template
 */
export function renderAliasSuggestions(context) {
  const suggestions = context._generateAliasSuggestions();
  
  if (suggestions.length === 0) {
    return "";
  }

  return html`
    <div class="alias-suggestions">
      <span class="suggestions-label">💡 Suggestions (click to add):</span>
      ${suggestions.map(suggestion => html`
        <span 
          class="suggestion-chip" 
          @click=${() => context._addSuggestedAlias(suggestion)}
          title="Click to add '${suggestion}'"
        >
          <span class="add-icon">+</span>
          ${suggestion}
        </span>
      `)}
    </div>
  `;
}

/**
 * Render the entity configuration dialog.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The dialog template
 */
export function renderEntityConfigDialog(context) {
  const entity = context._editingEntity;
  const draft = context._entityConfigDraft;

  return html`
    <div class="preview-overlay" @click=${(e) => {
      if (e.target === e.currentTarget) context._closeEntityConfigDialog();
    }}>
      <div class="entity-config-dialog">
        <h2>Configure Entity</h2>
        <div class="entity-id-subtitle">${entity.entity_id}</div>

        <div class="form-field">
          <label>Custom Name</label>
          <input
            type="text"
            .value=${draft.name || ""}
            @input=${(e) => context._entityConfigDraft = { ...draft, name: e.target.value }}
            placeholder="${entity.name || entity.entity_id}"
          />
          <div class="hint">Override the name Google will use for this entity</div>
        </div>

        <div class="form-field">
          <label>Aliases</label>
          <div class="alias-tags">
            ${draft.aliases.map(alias => html`
              <span class="alias-tag">
                ${alias}
                <button @click=${() => context._removeAlias(alias)}>×</button>
              </span>
            `)}
          </div>
          ${renderAliasSuggestions(context)}
          <div class="add-alias-row">
            <input
              type="text"
              .value=${draft._newAlias || ""}
              @input=${(e) => context._entityConfigDraft = { ...draft, _newAlias: e.target.value }}
              @keydown=${(e) => { if (e.key === "Enter") { e.preventDefault(); context._addAlias(); } }}
              placeholder="Add an alias..."
            />
            <button @click=${() => context._addAlias()}>Add</button>
          </div>
          <div class="hint">Alternative names Google will recognize (e.g., "bedroom light", "main lamp")</div>
        </div>

        <div class="form-field">
          <label>Room Hint</label>
          <input
            type="text"
            .value=${draft.room || ""}
            @input=${(e) => context._entityConfigDraft = { ...draft, room: e.target.value }}
            placeholder="e.g., Living Room, Kitchen"
          />
          <div class="hint">Suggest which room this entity belongs to in Google Home</div>
        </div>

        <div class="action-buttons">
          <button class="btn btn-secondary" @click=${() => context._closeEntityConfigDialog()}>
            Cancel
          </button>
          <button class="btn btn-primary" @click=${() => context._saveEntityConfig()}>
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render the migration notice dialog.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The migration template
 */
export function renderMigration(context) {
  const data = context._migrationData || {};

  return html`
    <div class="content">
      <div class="migration-notice">
        <h2>⚠️ Existing Configuration Detected</h2>
        <p>
          Found ${data.count || 0} entities in <code>${data.source_file || "unknown"}</code>.
          <br>
          ${data.exposed || 0} exposed, ${data.excluded || 0} excluded.
        </p>
        <p>
          <strong>Import existing entities</strong> to preserve your settings,
          or <strong>skip</strong> to start fresh with bulk rules.
        </p>
        <div style="display: flex; gap: 12px; justify-content: center; margin-top: 16px;">
          <button class="btn btn-primary" @click=${() => context._handleMigration("import")}>
            Import Existing
          </button>
          <button class="btn btn-secondary" @click=${() => context._handleMigration("skip")}>
            Skip & Start Fresh
          </button>
        </div>
      </div>
    </div>
  `;
}
