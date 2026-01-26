/**
 * Google Home Exposure Manager Panel
 * A custom panel for managing Google Assistant entity exposure.
 * 
 * This is the main component that orchestrates the UI. Rendering logic
 * is delegated to separate modules for maintainability:
 * - panel-styles.js: CSS styles
 * - panel-tabs.js: Tab content renderers
 * - panel-dialogs.js: Dialog renderers
 * - alias-suggestions.js: Alias generation logic
 */

import {
  LitElement,
  html,
} from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

import { panelStyles } from "/google_exposure_panel/panel-styles.js";
import { generateAliasSuggestions } from "/google_exposure_panel/alias-suggestions.js";
import { renderBulkRules, renderDevicesAndEntities, renderSettings } from "/google_exposure_panel/panel-tabs.js";
import { 
  renderPreviewDialog, 
  renderUnsavedDialog, 
  renderEntityConfigDialog, 
  renderMigration 
} from "/google_exposure_panel/panel-dialogs.js";

class GoogleExposurePanel extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      panel: { type: Object },
      _activeTab: { type: String },
      _config: { type: Object },
      _pendingConfig: { type: Object },
      _entities: { type: Array },
      _devices: { type: Array },
      _areas: { type: Array },
      _preview: { type: Object },
      _loading: { type: Boolean },
      _saving: { type: Boolean },
      _showPreview: { type: Boolean },
      _showUnsavedDialog: { type: Boolean },
      _pendingNavigation: { type: Object },
      _migrationNeeded: { type: Boolean },
      _migrationData: { type: Object },
      _hasChanges: { type: Boolean },
      _error: { type: String },
      _searchFilter: { type: String },
      _expandedDevices: { type: Object },
      _editingEntity: { type: Object },
      _entityConfigDraft: { type: Object },
      _showFiltered: { type: Boolean },
    };
  }

  static get styles() {
    return panelStyles;
  }

  constructor() {
    super();
    this._activeTab = "devices_entities";
    this._config = null;
    this._pendingConfig = null;
    this._entities = [];
    this._devices = [];
    this._areas = [];
    this._preview = null;
    this._loading = true;
    this._saving = false;
    this._showPreview = false;
    this._showUnsavedDialog = false;
    this._pendingNavigation = null;
    this._migrationNeeded = false;
    this._migrationData = null;
    this._hasChanges = false;
    this._error = null;
    this._searchFilter = "";
    this._expandedDevices = {};
    this._editingEntity = null;
    this._entityConfigDraft = {};
    this._showFiltered = false;
    this._boundBeforeUnload = this._handleBeforeUnload.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadData();
    window.addEventListener("beforeunload", this._boundBeforeUnload);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener("beforeunload", this._boundBeforeUnload);
  }

  // ============================================================
  // Data Loading & Persistence
  // ============================================================

  _handleBeforeUnload(e) {
    if (this._hasChanges) {
      e.preventDefault();
      e.returnValue = "";
      return "";
    }
  }

  async _loadData() {
    this._loading = true;
    this._error = null;

    try {
      const configResult = await this.hass.callWS({
        type: "google_home_exposure_manager/get_config",
      });

      this._config = configResult.config;
      this._pendingConfig = JSON.parse(JSON.stringify(configResult.config));
      this._migrationNeeded = configResult.migration_needed;
      this._migrationData = configResult.migration_data;

      const entitiesResult = await this.hass.callWS({
        type: "google_home_exposure_manager/get_entities",
      });
      this._entities = entitiesResult.entities;
      this._devices = entitiesResult.devices;
      this._areas = entitiesResult.areas;

    } catch (err) {
      console.error("Failed to load data:", err);
      this._error = err.message || "Failed to load configuration";
    }

    this._loading = false;
  }

  async _computePreview() {
    try {
      const result = await this.hass.callWS({
        type: "google_home_exposure_manager/compute_preview",
        config: this._pendingConfig,
      });
      this._preview = result;
      this._showPreview = true;
    } catch (err) {
      console.error("Failed to compute preview:", err);
      this._error = err.message || "Failed to compute preview";
    }
  }

  async _saveConfig() {
    this._saving = true;
    this._error = null;

    try {
      // Auto-generate aliases if enabled
      const configToSave = this._applyAutoAliases(this._pendingConfig);

      await this.hass.callWS({
        type: "google_home_exposure_manager/save_config",
        config: configToSave,
      });

      this._config = JSON.parse(JSON.stringify(configToSave));
      this._pendingConfig = JSON.parse(JSON.stringify(configToSave));
      this._hasChanges = false;
      this._showPreview = false;

      if (this._pendingNavigation?.type === "tab") {
        this._activeTab = this._pendingNavigation.tab;
        this._pendingNavigation = null;
      }

      await this._loadData();

    } catch (err) {
      console.error("Failed to save:", err);
      this._error = err.message || "Failed to save configuration";
    }

    this._saving = false;
  }

  async _handleMigration(action) {
    this._loading = true;

    try {
      await this.hass.callWS({
        type: "google_home_exposure_manager/handle_migration",
        action: action,
      });

      await this._loadData();

    } catch (err) {
      console.error("Migration failed:", err);
      this._error = err.message || "Migration failed";
      this._loading = false;
    }
  }

  // ============================================================
  // Navigation & State Management
  // ============================================================

  _setTab(tab) {
    if (this._migrationNeeded && tab !== "migration") {
      return;
    }
    if (this._hasChanges && tab !== this._activeTab) {
      this._pendingNavigation = { type: "tab", tab };
      this._showUnsavedDialog = true;
      return;
    }
    this._activeTab = tab;
  }

  _confirmNavigation() {
    this._pendingConfig = JSON.parse(JSON.stringify(this._config));
    this._hasChanges = false;
    this._showUnsavedDialog = false;

    if (this._pendingNavigation?.type === "tab") {
      this._activeTab = this._pendingNavigation.tab;
    }
    this._pendingNavigation = null;
  }

  async _saveAndNavigate() {
    this._showUnsavedDialog = false;
    await this._computePreview();
  }

  _cancelNavigation() {
    this._showUnsavedDialog = false;
    this._pendingNavigation = null;
  }

  // ============================================================
  // Config Helpers
  // ============================================================

  _updatePendingConfig(path, value) {
    const keys = path.split(".");
    let obj = this._pendingConfig;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!obj[keys[i]]) obj[keys[i]] = {};
      obj = obj[keys[i]];
    }

    obj[keys[keys.length - 1]] = value;
    this._hasChanges = true;
    this.requestUpdate();
  }

  _toggleDomain(domain) {
    const domains = this._pendingConfig?.bulk_rules?.expose_domains || [];
    const idx = domains.indexOf(domain);

    if (idx >= 0) {
      domains.splice(idx, 1);
    } else {
      domains.push(domain);
    }

    this._updatePendingConfig("bulk_rules.expose_domains", [...domains]);
  }

  _toggleArea(areaId) {
    const areas = this._pendingConfig?.bulk_rules?.exclude_areas || [];
    const idx = areas.indexOf(areaId);

    if (idx >= 0) {
      areas.splice(idx, 1);
    } else {
      areas.push(areaId);
    }

    this._updatePendingConfig("bulk_rules.exclude_areas", [...areas]);
  }

  _setEntityOverride(entityId, expose, source = 'selected') {
    const overrides = { ...(this._pendingConfig?.entity_overrides || {}) };

    if (expose === null) {
      delete overrides[entityId];
    } else {
      overrides[entityId] = { expose, source };
    }

    this._pendingConfig.entity_overrides = overrides;
    
    // After entity change, recalculate device implied state
    const entity = this._entities.find(e => e.entity_id === entityId);
    if (entity?.device_id) {
      this._recalculateDeviceState(entity.device_id);
    }
    
    this._hasChanges = true;
    this.requestUpdate();
  }

  _setDeviceOverride(deviceId, expose, source = 'selected') {
    const overrides = { ...(this._pendingConfig?.device_overrides || {}) };

    if (expose === null) {
      delete overrides[deviceId];
    } else {
      overrides[deviceId] = { expose, source };
    }

    this._pendingConfig.device_overrides = overrides;
    
    // After device change, propagate to entities
    this._propagateDeviceToEntities(deviceId, expose, source);
    
    this._hasChanges = true;
    this.requestUpdate();
  }

  /**
   * Get entity override info: { expose, source } or null if unset
   * Handles legacy data format (just expose boolean or missing source)
   */
  _getEntityOverrideInfo(entityId) {
    const override = this._pendingConfig?.entity_overrides?.[entityId];
    if (!override) return null;
    
    // Handle legacy format: { expose: bool } without source
    // Treat legacy data as 'selected' since user explicitly set it
    if (typeof override === 'object' && 'expose' in override) {
      return {
        expose: override.expose,
        source: override.source || 'selected'
      };
    }
    // Handle very old format: entityId: true/false
    if (typeof override === 'boolean') {
      return { expose: override, source: 'selected' };
    }
    return null;
  }

  _getEntityOverride(entityId) {
    const info = this._getEntityOverrideInfo(entityId);
    return info ? info.expose : null;
  }

  /**
   * Get device override info: { expose, source } or null if unset
   * Handles legacy data format (just expose boolean or missing source)
   */
  _getDeviceOverrideInfo(deviceId) {
    const override = this._pendingConfig?.device_overrides?.[deviceId];
    if (!override) return null;
    
    // Handle legacy format: { expose: bool } without source
    if (typeof override === 'object' && 'expose' in override) {
      return {
        expose: override.expose,
        source: override.source || 'selected'
      };
    }
    // Handle very old format: deviceId: true/false
    if (typeof override === 'boolean') {
      return { expose: override, source: 'selected' };
    }
    return null;
  }

  _getDeviceOverride(deviceId) {
    const info = this._getDeviceOverrideInfo(deviceId);
    return info ? info.expose : null;
  }

  /**
   * Propagate device state to all non-filtered entities.
   * When device is selected/implied, entities become implied.
   * When device is unset (expose === null), entities become unset.
   */
  _propagateDeviceToEntities(deviceId, expose, deviceSource) {
    const deviceEntities = this._entities.filter(e => e.device_id === deviceId);
    const overrides = { ...(this._pendingConfig?.entity_overrides || {}) };
    
    for (const entity of deviceEntities) {
      // Skip filtered entities
      if (this._isEntityFiltered(entity.entity_id)) {
        continue;
      }
      
      // Use the normalized getter to handle legacy data
      const currentOverride = this._getEntityOverrideInfo(entity.entity_id);
      
      if (expose === null) {
        // Device unset - clear implied entities, keep selected ones
        if (currentOverride?.source === 'implied') {
          delete overrides[entity.entity_id];
        }
      } else {
        // Device set - set entities to implied (unless already selected)
        if (!currentOverride || currentOverride.source === 'implied') {
          overrides[entity.entity_id] = { expose, source: 'implied' };
        }
        // If entity is selected, leave it alone
      }
    }
    
    this._pendingConfig.entity_overrides = overrides;
  }

  /**
   * Recalculate device state based on entity states.
   * If all non-filtered entities are selected with same value, device becomes implied.
   * Otherwise device becomes unset (unless already selected).
   */
  _recalculateDeviceState(deviceId) {
    const deviceEntities = this._entities.filter(e => e.device_id === deviceId);
    const activeEntities = deviceEntities.filter(e => !this._isEntityFiltered(e.entity_id));
    
    if (activeEntities.length === 0) {
      return;
    }
    
    const deviceOverride = this._getDeviceOverrideInfo(deviceId);
    
    // Don't override a selected device state
    if (deviceOverride?.source === 'selected') {
      return;
    }
    
    // Check if all active entities are selected with the same expose value
    let allSelected = true;
    let allSameValue = true;
    let firstValue = null;
    
    for (const entity of activeEntities) {
      const override = this._getEntityOverrideInfo(entity.entity_id);
      if (!override || override.source !== 'selected') {
        allSelected = false;
        break;
      }
      if (firstValue === null) {
        firstValue = override.expose;
      } else if (override.expose !== firstValue) {
        allSameValue = false;
        break;
      }
    }
    
    const overrides = { ...(this._pendingConfig?.device_overrides || {}) };
    
    if (allSelected && allSameValue && firstValue !== null) {
      // All entities selected with same value - device becomes implied
      overrides[deviceId] = { expose: firstValue, source: 'implied' };
    } else {
      // Mixed or not all selected - device becomes unset (if it was implied)
      if (deviceOverride?.source === 'implied') {
        delete overrides[deviceId];
      }
    }
    
    this._pendingConfig.device_overrides = overrides;
  }

  /**
   * Handle entity button click.
   * - If unset or implied → becomes selected
   * - If selected → becomes unset
   */
  _handleEntityButtonClick(entityId, targetExpose) {
    const currentOverride = this._getEntityOverrideInfo(entityId);
    
    if (currentOverride?.expose === targetExpose && currentOverride?.source === 'selected') {
      // Already selected with this value - unset it
      this._setEntityOverride(entityId, null);
    } else {
      // Unset, implied, or selected with different value - set to selected
      this._setEntityOverride(entityId, targetExpose, 'selected');
    }
  }

  /**
   * Handle device button click.
   * - If unset or implied → becomes selected (entities become implied)
   * - If selected → becomes unset (implied entities become unset)
   */
  _handleDeviceButtonClick(deviceId, targetExpose) {
    const currentOverride = this._getDeviceOverrideInfo(deviceId);
    
    if (currentOverride?.expose === targetExpose && currentOverride?.source === 'selected') {
      // Already selected with this value - unset it
      this._setDeviceOverride(deviceId, null);
    } else {
      // Unset, implied, or selected with different value - set to selected
      this._setDeviceOverride(deviceId, targetExpose, 'selected');
    }
  }

  /**
   * Get count of non-filtered entities for a device.
   */
  _getNonFilteredEntityCount(deviceId) {
    const deviceEntities = this._entities.filter(e => e.device_id === deviceId);
    return deviceEntities.filter(e => !this._isEntityFiltered(e.entity_id)).length;
  }

  _getEntityConfig(entityId) {
    return this._pendingConfig?.entity_config?.[entityId] || {};
  }

  _hasEntityConfig(entityId) {
    const config = this._getEntityConfig(entityId);
    return config.name || (config.aliases && config.aliases.length > 0) || config.room;
  }

  _applyAutoAliases(config) {
    // If auto_aliases is disabled, return config as-is
    const autoAliases = config?.settings?.auto_aliases;
    if (autoAliases === false) {
      return config;
    }

    // Get exposed entities from preview
    const exposedEntities = this._preview?.exposed || [];
    if (exposedEntities.length === 0) {
      return config;
    }

    // Deep clone config
    const newConfig = JSON.parse(JSON.stringify(config));
    if (!newConfig.entity_config) {
      newConfig.entity_config = {};
    }

    // Generate aliases for exposed entities that don't have custom aliases
    for (const entityId of exposedEntities) {
      const existingConfig = newConfig.entity_config[entityId] || {};
      
      // Skip if entity already has manually configured aliases
      if (existingConfig.aliases && existingConfig.aliases.length > 0) {
        continue;
      }

      // Find entity info
      const entity = this._entities.find(e => e.entity_id === entityId);
      if (!entity) continue;

      const baseName = existingConfig.name || entity.name || entityId.split(".")[1].replace(/_/g, " ");
      const suggestions = generateAliasSuggestions(baseName, [], 5);

      if (suggestions.length > 0) {
        if (!newConfig.entity_config[entityId]) {
          newConfig.entity_config[entityId] = {};
        }
        newConfig.entity_config[entityId].aliases = suggestions;
      }
    }

    return newConfig;
  }

  // ============================================================
  // Navigation
  // ============================================================

  _navigateTo(path) {
    // Use Home Assistant's in-app navigation
    history.pushState(null, "", path);
    window.dispatchEvent(new CustomEvent("location-changed"));
  }

  // ============================================================
  // Entity Config Dialog
  // ============================================================

  _openEntityConfigDialog(entity) {
    const currentConfig = this._getEntityConfig(entity.entity_id);
    this._editingEntity = entity;
    this._entityConfigDraft = {
      name: currentConfig.name || "",
      aliases: [...(currentConfig.aliases || [])],
      room: currentConfig.room || "",
      _newAlias: "",
    };
  }

  _closeEntityConfigDialog() {
    this._editingEntity = null;
    this._entityConfigDraft = {};
  }

  _addAlias() {
    const alias = this._entityConfigDraft._newAlias?.trim();
    if (alias && !this._entityConfigDraft.aliases.includes(alias)) {
      this._entityConfigDraft = {
        ...this._entityConfigDraft,
        aliases: [...this._entityConfigDraft.aliases, alias],
        _newAlias: "",
      };
    }
  }

  _removeAlias(alias) {
    this._entityConfigDraft = {
      ...this._entityConfigDraft,
      aliases: this._entityConfigDraft.aliases.filter(a => a !== alias),
    };
  }

  _generateAliasSuggestions() {
    const entity = this._editingEntity;
    const draft = this._entityConfigDraft;
    const baseName = draft.name || entity.name || entity.entity_id.split(".")[1].replace(/_/g, " ");
    return generateAliasSuggestions(baseName, draft.aliases);
  }

  _addSuggestedAlias(alias) {
    if (!this._entityConfigDraft.aliases.includes(alias)) {
      this._entityConfigDraft = {
        ...this._entityConfigDraft,
        aliases: [...this._entityConfigDraft.aliases, alias],
      };
    }
  }

  _saveEntityConfig() {
    const entityId = this._editingEntity.entity_id;
    const config = {
      ...(this._entityConfigDraft.name ? { name: this._entityConfigDraft.name } : {}),
      ...(this._entityConfigDraft.aliases.length > 0 ? { aliases: this._entityConfigDraft.aliases } : {}),
      ...(this._entityConfigDraft.room ? { room: this._entityConfigDraft.room } : {}),
    };

    const entityConfig = { ...(this._pendingConfig?.entity_config || {}) };
    
    if (Object.keys(config).length > 0) {
      entityConfig[entityId] = config;
    } else {
      delete entityConfig[entityId];
    }

    this._updatePendingConfig("entity_config", entityConfig);
    this._closeEntityConfigDialog();
  }

  // ============================================================
  // Device/Entity Helpers
  // ============================================================

  _toggleDeviceExpanded(deviceId) {
    this._expandedDevices = {
      ...this._expandedDevices,
      [deviceId]: !this._expandedDevices[deviceId],
    };
  }

  // ============================================================
  // Filter Entities and Devices from List
  // ============================================================

  _isEntityFiltered(entityId) {
    const filtered = this._pendingConfig?.filtered_entities || [];
    return filtered.includes(entityId);
  }

  _isDeviceFiltered(deviceId) {
    const filtered = this._pendingConfig?.filtered_devices || [];
    return filtered.includes(deviceId);
  }

  _toggleEntityFiltered(entityId) {
    const filtered = [...(this._pendingConfig?.filtered_entities || [])];
    const idx = filtered.indexOf(entityId);
    if (idx >= 0) {
      filtered.splice(idx, 1);
    } else {
      filtered.push(entityId);
    }
    this._updatePendingConfig("filtered_entities", filtered);
  }

  _toggleDeviceFiltered(deviceId) {
    const filtered = [...(this._pendingConfig?.filtered_devices || [])];
    const idx = filtered.indexOf(deviceId);
    if (idx >= 0) {
      filtered.splice(idx, 1);
    } else {
      filtered.push(deviceId);
    }
    this._updatePendingConfig("filtered_devices", filtered);
  }

  _getFilteredCount() {
    const filteredEntities = this._pendingConfig?.filtered_entities?.length || 0;
    const filteredDevices = this._pendingConfig?.filtered_devices?.length || 0;
    return filteredEntities + filteredDevices;
  }

  // ============================================================
  // Main Render
  // ============================================================

  render() {
    if (this._loading) {
      return html`
        <div class="container">
          <div class="loading">Loading...</div>
        </div>
      `;
    }

    const tabs = [
      { id: "devices_entities", label: "Devices & Entities" },
      { id: "bulk_rules", label: "Bulk Rules" },
      { id: "settings", label: "Settings" },
    ];

    return html`
      <div class="container">
        <div class="header">
          <h1>
            <svg class="header-icon" viewBox="0 0 128 128">
              <defs>
                <linearGradient id="homeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#03A9F4"/>
                  <stop offset="100%" style="stop-color:#4CAF50"/>
                </linearGradient>
                <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#4CAF50"/>
                  <stop offset="100%" style="stop-color:#8BC34A"/>
                </linearGradient>
              </defs>
              <path fill="url(#homeGrad)" d="M64 16L16 56V112C16 114.2 17.8 116 20 116H52V80H76V116H108C110.2 116 112 114.2 112 112V56L64 16Z"/>
              <path fill="#1976D2" d="M64 16L16 56H28L64 26L100 56H112L64 16Z"/>
              <path fill="none" stroke="url(#waveGrad)" stroke-width="4" stroke-linecap="round" d="M80 36 Q92 32 96 20"/>
              <path fill="none" stroke="url(#waveGrad)" stroke-width="3.5" stroke-linecap="round" d="M84 42 Q100 36 108 22"/>
              <path fill="none" stroke="url(#waveGrad)" stroke-width="3" stroke-linecap="round" d="M88 48 Q106 42 118 26"/>
              <circle cx="100" cy="16" r="6" fill="#4CAF50"/>
              <circle cx="112" cy="24" r="5" fill="#8BC34A"/>
              <circle cx="120" cy="34" r="4" fill="#CDDC39"/>
            </svg>
            Google Home Exposure Manager
          </h1>
        </div>

        ${this._error ? html`
          <div class="error-banner">${this._error}</div>
        ` : ""}

        ${this._migrationNeeded ? renderMigration(this) : html`
          <div class="tabs">
            ${tabs.map(tab => html`
              <div
                class="tab ${this._activeTab === tab.id ? "active" : ""}"
                @click=${() => this._setTab(tab.id)}
              >
                ${tab.label}
              </div>
            `)}
          </div>

          <div class="content">
            ${this._renderTabContent()}

            <div class="action-buttons">
              <button
                class="btn btn-secondary"
                @click=${() => {
                  this._pendingConfig = JSON.parse(JSON.stringify(this._config));
                  this._hasChanges = false;
                }}
                ?disabled=${!this._hasChanges}
              >
                Reset Changes
              </button>
              <button
                class="btn btn-primary"
                @click=${() => this._computePreview()}
                ?disabled=${!this._hasChanges || this._saving}
              >
                Preview & Save
              </button>
            </div>
          </div>
        `}
      </div>

      ${this._showPreview ? renderPreviewDialog(this) : ""}
      ${this._showUnsavedDialog ? renderUnsavedDialog(this) : ""}
      ${this._editingEntity ? renderEntityConfigDialog(this) : ""}
    `;
  }

  _renderTabContent() {
    switch (this._activeTab) {
      case "bulk_rules":
        return renderBulkRules(this);
      case "devices_entities":
        return renderDevicesAndEntities(this);
      case "settings":
        return renderSettings(this);
      default:
        return html`<p>Unknown tab</p>`;
    }
  }
}

customElements.define("google-exposure-panel", GoogleExposurePanel);
