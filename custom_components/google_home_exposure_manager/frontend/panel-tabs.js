/**
 * Tab content renderers for Google Home Exposure Manager Panel
 * Contains rendering logic for bulk rules, devices/entities, and settings tabs.
 */

import { html } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

/**
 * Render the bulk rules tab content.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The tab content template
 */
export function renderBulkRules(context) {
  const domains = [
    "light", "switch", "cover", "fan", "climate", "lock", 
    "sensor", "binary_sensor", "camera", "media_player", 
    "vacuum", "humidifier", "scene", "script"
  ];
  const selectedDomains = context._pendingConfig?.bulk_rules?.expose_domains || [];
  const selectedAreas = context._pendingConfig?.bulk_rules?.exclude_areas || [];
  const patterns = (context._pendingConfig?.bulk_rules?.exclude_patterns || []).join("\n");

  return html`
    <div class="section">
      <div class="section-title">Auto-Expose Domains</div>
      <div class="section-description">Select which entity domains to expose to Google Assistant by default.</div>
      <div class="chip-container">
        ${domains.map(domain => html`
          <div
            class="chip ${selectedDomains.includes(domain) ? "selected" : ""}"
            @click=${() => context._toggleDomain(domain)}
          >
            ${domain}
          </div>
        `)}
      </div>
    </div>

    <div class="section">
      <div class="section-title">Exclude Areas</div>
      <div class="section-description">Entities in these areas will not be exposed.</div>
      <div class="chip-container">
        ${context._areas.map(area => html`
          <div
            class="chip ${selectedAreas.includes(area.area_id) ? "selected" : ""}"
            @click=${() => context._toggleArea(area.area_id)}
          >
            ${area.name}
          </div>
        `)}
      </div>
    </div>

    <div class="section">
      <div class="section-title">Exclude Patterns</div>
      <div class="section-description">
        Glob patterns to exclude entities (one per line). Supports * wildcards.
        <br>Example: *_battery, sensor.temperature_*
      </div>
      <textarea
        .value=${patterns}
        @input=${(e) => context._updatePendingConfig(
          "bulk_rules.exclude_patterns",
          e.target.value.split("\n").filter(p => p.trim())
        )}
        placeholder="*_battery&#10;sensor.temperature_*"
      ></textarea>
    </div>
  `;
}

/**
 * Render the settings tab content.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The tab content template
 */
export function renderSettings(context) {
  const settings = context._pendingConfig?.settings || {};

  return html`
    <div class="section">
      <div class="section-title">Integration Settings</div>

      <label class="checkbox-label">
        <input
          type="checkbox"
          .checked=${settings.backups !== false}
          @change=${(e) => context._updatePendingConfig("settings.backups", e.target.checked)}
        />
        Create backups before modifying files
      </label>

      <label class="checkbox-label">
        <input
          type="checkbox"
          .checked=${settings.auto_aliases !== false}
          @change=${(e) => context._updatePendingConfig("settings.auto_aliases", e.target.checked)}
        />
        Auto-generate common aliases for exposed entities
        <span class="setting-hint">Adds natural spoken variations like "lights" → "lamps", room name alternatives, etc.</span>
      </label>
    </div>

    <div class="sync-notice">
      <strong>Note:</strong> After saving, say "Hey Google, sync my devices" to update Google Home with your changes.
    </div>
  `;
}

/**
 * Render a single entity item row.
 * @param {Object} context - The panel component instance (this)
 * @param {Object} entity - The entity object
 * @returns {TemplateResult} The entity item template
 */
export function renderEntityItem(context, entity) {
  const overrideInfo = context._getEntityOverrideInfo(entity.entity_id);
  const area = context._areas.find(a => a.area_id === entity.area_id);
  const hasConfig = context._hasEntityConfig(entity.entity_id);
  const config = context._getEntityConfig(entity.entity_id);
  const aliases = config.aliases || [];
  const isFiltered = context._isEntityFiltered(entity.entity_id);
  
  // Three states: selected, implied, unset
  const exposeSelected = overrideInfo?.expose === true && overrideInfo?.source === 'selected';
  const exposeImplied = overrideInfo?.expose === true && overrideInfo?.source === 'implied';
  const excludeSelected = overrideInfo?.expose === false && overrideInfo?.source === 'selected';
  const excludeImplied = overrideInfo?.expose === false && overrideInfo?.source === 'implied';
  
  return html`
    <div class="entity-item ${isFiltered ? 'filtered-item' : ''}">
      <div class="entity-info">
        <div class="entity-name-row">
          <span class="entity-name">
            ${config.name || entity.name || entity.entity_id}
          </span>
          <button 
            class="nav-link-btn" 
            @click=${(e) => { 
              e.stopPropagation(); 
              context._navigateTo(`/config/entities/entity/${entity.entity_id}`);
            }}
            title="View in Home Assistant"
          >
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z" /></svg>
          </button>
        </div>
        <span class="entity-id">
          ${entity.entity_id}
          ${area && !entity.device_id ? ` • ${area.name}` : ''}
        </span>
        ${aliases.length > 0 ? html`
          <div class="entity-aliases">
            <span class="aliases-label">Aliases:</span>
            ${aliases.map(alias => html`<span class="alias-pill">${alias}</span>`)}
          </div>
        ` : ''}
        ${config.room ? html`<div class="entity-room">📍 ${config.room}</div>` : ''}
      </div>
      <div class="entity-status">
        <button
          class="filter-btn ${isFiltered ? 'is-filtered' : ''}"
          @click=${(e) => { e.stopPropagation(); context._toggleEntityFiltered(entity.entity_id); }}
          title="${isFiltered ? 'Show in list' : 'Filter from list'}"
        >
          ${isFiltered ? '👁' : '👁‍🗨'}
        </button>
        <button
          class="edit-btn ${hasConfig ? 'has-config' : ''}"
          @click=${(e) => { e.stopPropagation(); context._openEntityConfigDialog(entity); }}
          title="Configure name, aliases, and room"
        >
          ✏️ Config
        </button>
        <button
          class="status-btn expose ${exposeSelected ? 'selected' : ''} ${exposeImplied ? 'implied' : ''}"
          @click=${() => context._handleEntityButtonClick(entity.entity_id, true)}
          title="${exposeSelected ? 'Selected - click to unset' : exposeImplied ? 'Implied from device - click to select' : 'Click to expose'}"
        >
          Expose${exposeImplied ? ' ⬆' : ''}
        </button>
        <button
          class="status-btn exclude ${excludeSelected ? 'selected' : ''} ${excludeImplied ? 'implied' : ''}"
          @click=${() => context._handleEntityButtonClick(entity.entity_id, false)}
          title="${excludeSelected ? 'Selected - click to unset' : excludeImplied ? 'Implied from device - click to select' : 'Click to exclude'}"
        >
          Exclude${excludeImplied ? ' ⬆' : ''}
        </button>
      </div>
    </div>
  `;
}

/**
 * Render a device group with expandable entity list.
 * @param {Object} context - The panel component instance (this)
 * @param {Object} device - The device object
 * @param {Array} deviceEntities - Entities belonging to this device
 * @param {string} filter - Current search filter
 * @returns {TemplateResult} The device group template
 */
export function renderDeviceGroup(context, device, deviceEntities, filter) {
  const isExpanded = context._expandedDevices[device.id];
  const isDeviceFiltered = context._isDeviceFiltered(device.id);
  
  // Get device override info for three-state display
  const deviceOverrideInfo = context._getDeviceOverrideInfo(device.id);
  const nonFilteredCount = context._getNonFilteredEntityCount(device.id);
  
  // Three states: selected, implied, unset
  const exposeSelected = deviceOverrideInfo?.expose === true && deviceOverrideInfo?.source === 'selected';
  const exposeImplied = deviceOverrideInfo?.expose === true && deviceOverrideInfo?.source === 'implied';
  const excludeSelected = deviceOverrideInfo?.expose === false && deviceOverrideInfo?.source === 'selected';
  const excludeImplied = deviceOverrideInfo?.expose === false && deviceOverrideInfo?.source === 'implied';
  
  // Filter entities for display: apply search and optionally show filtered entities
  let filteredDeviceEntities = deviceEntities;
  if (!context._showFiltered) {
    filteredDeviceEntities = filteredDeviceEntities.filter(e => !context._isEntityFiltered(e.entity_id));
  }
  if (filter) {
    filteredDeviceEntities = filteredDeviceEntities.filter(e =>
      e.entity_id.toLowerCase().includes(filter) ||
      (e.name && e.name.toLowerCase().includes(filter))
    );
  }
  
  const area = context._areas.find(a => a.area_id === device.area_id);
  
  return html`
    <div class="device-group ${isDeviceFiltered ? 'filtered-item' : ''}">
      <div class="device-header" @click=${() => context._toggleDeviceExpanded(device.id)}>
        <div class="device-header-left">
          <svg class="expand-icon ${isExpanded ? 'expanded' : ''}" viewBox="0 0 24 24">
            <path fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
          </svg>
          <div class="device-info">
            <div class="device-name-row">
              <span class="device-name">${device.name}</span>
              <button 
                class="nav-link-btn" 
                @click=${(e) => { 
                  e.stopPropagation(); 
                  context._navigateTo(`/config/devices/device/${device.id}`);
                }}
                title="View device in Home Assistant"
              >
                <svg viewBox="0 0 24 24"><path fill="currentColor" d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z" /></svg>
              </button>
            </div>
            <div class="device-meta">
              <span>${deviceEntities.length} entit${deviceEntities.length !== 1 ? 'ies' : 'y'}</span>
              ${nonFilteredCount !== deviceEntities.length ? html`<span>(${nonFilteredCount} active)</span>` : ''}
              ${area ? html`<span>• ${area.name}</span>` : ''}
              ${filter && filteredDeviceEntities.length !== deviceEntities.length ? html`
                <span>• ${filteredDeviceEntities.length} matching</span>
              ` : ''}
            </div>
          </div>
        </div>
        <div class="entity-status" @click=${(e) => e.stopPropagation()}>
          <button
            class="filter-btn ${isDeviceFiltered ? 'is-filtered' : ''}"
            @click=${() => context._toggleDeviceFiltered(device.id)}
            title="${isDeviceFiltered ? 'Show in list' : 'Filter from list'}"
          >
            ${isDeviceFiltered ? '👁' : '👁‍🗨'}
          </button>
          <button
            class="status-btn expose ${exposeSelected ? 'selected' : ''} ${exposeImplied ? 'implied' : ''}"
            @click=${() => context._handleDeviceButtonClick(device.id, true)}
            title="${exposeSelected ? 'Selected - click to unset' : exposeImplied ? 'Implied from entities - click to select' : 'Click to expose all'}"
            ?disabled=${nonFilteredCount === 0}
          >
            Expose All${exposeImplied ? ' ⬇' : ''}
          </button>
          <button
            class="status-btn exclude ${excludeSelected ? 'selected' : ''} ${excludeImplied ? 'implied' : ''}"
            @click=${() => context._handleDeviceButtonClick(device.id, false)}
            title="${excludeSelected ? 'Selected - click to unset' : excludeImplied ? 'Implied from entities - click to select' : 'Click to exclude all'}"
            ?disabled=${nonFilteredCount === 0}
          >
            Exclude All${excludeImplied ? ' ⬇' : ''}
          </button>
        </div>
      </div>
      
      ${isExpanded ? html`
        <div class="device-entities">
          ${filteredDeviceEntities.map(entity => renderEntityItem(context, entity))}
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * Render the devices and entities tab content.
 * @param {Object} context - The panel component instance (this)
 * @returns {TemplateResult} The tab content template
 */
export function renderDevicesAndEntities(context) {
  const filter = context._searchFilter.toLowerCase();
  const filteredCount = context._getFilteredCount();
  
  const entitiesByDevice = {};
  const standaloneEntities = [];
  
  context._entities.forEach(entity => {
    if (entity.device_id) {
      if (!entitiesByDevice[entity.device_id]) {
        entitiesByDevice[entity.device_id] = [];
      }
      entitiesByDevice[entity.device_id].push(entity);
    } else {
      standaloneEntities.push(entity);
    }
  });
  
  // Filter devices: search + filtered
  let filteredDevices = context._devices.filter(device => {
    // Check if device is filtered
    if (!context._showFiltered && context._isDeviceFiltered(device.id)) {
      return false;
    }
    
    if (!filter) return true;
    
    if (device.name.toLowerCase().includes(filter)) return true;
    
    const deviceEntities = entitiesByDevice[device.id] || [];
    return deviceEntities.some(e => 
      e.entity_id.toLowerCase().includes(filter) ||
      (e.name && e.name.toLowerCase().includes(filter))
    );
  });
  
  // Filter standalone: search + filtered
  let filteredStandalone = standaloneEntities.filter(e => {
    // Check if entity is filtered
    if (!context._showFiltered && context._isEntityFiltered(e.entity_id)) {
      return false;
    }
    
    return !filter ||
      e.entity_id.toLowerCase().includes(filter) ||
      (e.name && e.name.toLowerCase().includes(filter));
  });
  
  const totalResults = filteredDevices.length + filteredStandalone.length;

  return html`
    <div class="section">
      <div class="section-title">Devices & Entities</div>
      <div class="section-description">
        Expand devices to see and control their entities. Set rules at device or entity level. Exclusions always win.
      </div>

      <div class="search-row">
        <input
          type="text"
          class="search-box"
          placeholder="Search devices or entities..."
          .value=${context._searchFilter}
          @input=${(e) => { context._searchFilter = e.target.value; context.requestUpdate(); }}
        />
        ${filteredCount > 0 ? html`
          <label class="show-filtered-toggle">
            <input
              type="checkbox"
              .checked=${context._showFiltered}
              @change=${(e) => { context._showFiltered = e.target.checked; context.requestUpdate(); }}
            />
            Show filtered (${filteredCount})
          </label>
        ` : ''}
      </div>

      ${filter ? html`
        <div class="search-results-info">
          Found ${filteredDevices.length} device${filteredDevices.length !== 1 ? 's' : ''} and 
          ${filteredStandalone.length} standalone entit${filteredStandalone.length !== 1 ? 'ies' : 'y'}
          ${filter ? ` matching "${filter}"` : ''}
        </div>
      ` : ''}

      ${totalResults === 0 ? html`
        <div class="no-results">
          No devices or entities found${filter ? ` matching "${filter}"` : ''}.
          ${filteredCount > 0 && !context._showFiltered ? html`<br><em>${filteredCount} filtered items not shown.</em>` : ''}
        </div>
      ` : ''}

      ${filteredDevices.map(device => renderDeviceGroup(context, device, entitiesByDevice[device.id] || [], filter))}

      ${filteredStandalone.length > 0 ? html`
        <div class="standalone-section">
          <div class="section-title">
            <svg class="standalone-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M6,2H18A2,2 0 0,1 20,4V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V4A2,2 0 0,1 6,2M6,4V8H18V4H6M6,10V14H18V10H6M6,16V20H18V16H6Z" />
            </svg>
            Standalone Entities (${filteredStandalone.length})
          </div>
          <div class="entity-list">
            ${filteredStandalone.slice(0, 50).map(entity => renderEntityItem(context, entity))}
          </div>
          ${filteredStandalone.length > 50 ? html`
            <p style="color: var(--secondary-text-color); font-size: 14px; margin-top: 8px;">
              Showing 50 of ${filteredStandalone.length} standalone entities. Use search to filter.
            </p>
          ` : ''}
        </div>
      ` : ''}
    </div>
  `;
}
