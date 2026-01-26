/**
 * CSS styles for Google Home Exposure Manager Panel
 */

import { css } from "https://unpkg.com/lit-element@2.4.0/lit-element.js?module";

export const panelStyles = css`
  :host {
    display: block;
    height: 100%;
    background: var(--primary-background-color);
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 400;
    color: var(--primary-text-color);
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-icon {
    width: 32px;
    height: 32px;
    color: var(--primary-color);
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--divider-color);
    margin-bottom: 16px;
    overflow-x: auto;
  }

  .tab {
    padding: 12px 24px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    color: var(--secondary-text-color);
    font-weight: 500;
    white-space: nowrap;
    transition: all 0.2s;
  }

  .tab:hover {
    color: var(--primary-text-color);
    background: var(--secondary-background-color);
  }

  .tab.active {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
  }

  .tab.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .content {
    background: var(--card-background-color);
    border-radius: 8px;
    padding: 16px;
    box-shadow: var(--ha-card-box-shadow, 0 2px 4px rgba(0,0,0,0.1));
  }

  .section {
    margin-bottom: 24px;
  }

  .section-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--primary-text-color);
  }

  .section-description {
    color: var(--secondary-text-color);
    font-size: 14px;
    margin-bottom: 16px;
  }

  .chip-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color);
  }

  .chip.selected {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .chip:hover:not(.selected) {
    background: var(--secondary-background-color);
  }

  .entity-list {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid var(--divider-color);
    border-radius: 4px;
  }

  .entity-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--divider-color);
  }

  .entity-item:last-child {
    border-bottom: none;
  }

  .entity-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }

  .entity-name-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .entity-name {
    font-weight: 500;
    color: var(--primary-text-color);
  }

  .nav-link-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    padding: 2px;
    border: none;
    border-radius: 4px;
    background: var(--secondary-background-color);
    color: var(--primary-color);
    cursor: pointer;
    opacity: 0.7;
    transition: opacity 0.2s, background 0.2s;
  }

  .nav-link-btn:hover {
    opacity: 1;
    background: var(--primary-color);
    color: white;
  }

  .nav-link-btn svg {
    width: 14px;
    height: 14px;
  }

  .entity-id {
    font-size: 12px;
    color: var(--secondary-text-color);
  }

  .entity-aliases {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }

  .aliases-label {
    font-size: 11px;
    color: var(--secondary-text-color);
  }

  .alias-pill {
    font-size: 11px;
    padding: 1px 6px;
    background: var(--secondary-background-color);
    border-radius: 10px;
    color: var(--secondary-text-color);
  }

  .entity-room {
    font-size: 11px;
    color: var(--secondary-text-color);
  }

  .entity-status {
    display: flex;
    gap: 8px;
  }

  .status-btn {
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color);
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
  }

  .status-btn.expose {
    border-color: var(--success-color, #4caf50);
    color: var(--success-color, #4caf50);
  }

  .status-btn.expose.selected,
  .status-btn.expose.active {
    background: var(--success-color, #4caf50);
    color: white;
  }

  .status-btn.expose.implied,
  .status-btn.expose.inherited,
  .status-btn.expose.computed {
    background: rgba(76, 175, 80, 0.15);
    border-style: dashed;
  }

  .status-btn.exclude {
    border-color: var(--error-color, #f44336);
    color: var(--error-color, #f44336);
  }

  .status-btn.exclude.selected,
  .status-btn.exclude.active {
    background: var(--error-color, #f44336);
    color: white;
  }

  .status-btn.exclude.implied,
  .status-btn.exclude.inherited,
  .status-btn.exclude.computed {
    background: rgba(244, 67, 54, 0.15);
    border-style: dashed;
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--divider-color);
  }

  .btn {
    padding: 10px 24px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn-primary {
    background: var(--primary-color);
    color: white;
  }

  .btn-primary:hover {
    opacity: 0.9;
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: var(--secondary-background-color);
    color: var(--primary-text-color);
  }

  .search-box {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--divider-color);
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 16px;
    background: var(--card-background-color);
    color: var(--primary-text-color);
  }

  .search-box:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  textarea {
    width: 100%;
    min-height: 100px;
    padding: 10px 12px;
    border: 1px solid var(--divider-color);
    border-radius: 4px;
    font-size: 14px;
    font-family: monospace;
    resize: vertical;
    background: var(--card-background-color);
    color: var(--primary-text-color);
  }

  .checkbox-label {
    display: flex;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
    cursor: pointer;
    padding: 8px 0;
  }

  .checkbox-label input {
    width: 18px;
    height: 18px;
    margin-top: 2px;
  }

  .setting-hint {
    display: block;
    width: 100%;
    font-size: 12px;
    color: var(--secondary-text-color);
    margin-left: 26px;
    margin-top: -4px;
  }

  .preview-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .preview-dialog {
    background: var(--card-background-color);
    border-radius: 8px;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    padding: 24px;
  }

  .preview-dialog h2 {
    margin: 0 0 16px 0;
    font-size: 20px;
  }

  .preview-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }

  .stat-card {
    padding: 16px;
    border-radius: 8px;
    text-align: center;
  }

  .stat-card.exposed {
    background: rgba(76, 175, 80, 0.1);
    color: var(--success-color, #4caf50);
  }

  .stat-card.excluded {
    background: rgba(244, 67, 54, 0.1);
    color: var(--error-color, #f44336);
  }

  .stat-card.unset {
    background: rgba(158, 158, 158, 0.1);
    color: var(--secondary-text-color);
  }

  .stat-number {
    font-size: 32px;
    font-weight: 500;
  }

  .stat-label {
    font-size: 14px;
    margin-top: 4px;
  }

  .exclusion-breakdown {
    background: var(--secondary-background-color);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
  }

  .breakdown-title {
    font-weight: 500;
    margin-bottom: 8px;
    font-size: 14px;
  }

  .breakdown-items {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .breakdown-item {
    font-size: 13px;
    color: var(--secondary-text-color);
  }

  .preview-section {
    margin-top: 16px;
  }

  .preview-section summary {
    cursor: pointer;
    padding: 8px;
    background: var(--secondary-background-color);
    border-radius: 4px;
    font-weight: 500;
  }

  .preview-list {
    max-height: 200px;
    overflow-y: auto;
    padding: 8px;
    font-size: 13px;
    font-family: monospace;
  }

  .migration-notice {
    background: rgba(255, 152, 0, 0.1);
    border: 1px solid var(--warning-color, #ff9800);
    border-radius: 8px;
    padding: 24px;
    text-align: center;
  }

  .migration-notice h2 {
    color: var(--warning-color, #ff9800);
    margin: 0 0 12px 0;
  }

  .migration-notice p {
    margin: 0 0 16px 0;
    color: var(--primary-text-color);
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px;
    color: var(--secondary-text-color);
  }

  .error-banner {
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid var(--error-color, #f44336);
    color: var(--error-color, #f44336);
    padding: 12px 16px;
    border-radius: 4px;
    margin-bottom: 16px;
  }

  .sync-notice {
    background: rgba(33, 150, 243, 0.1);
    border: 1px solid var(--info-color, #2196f3);
    color: var(--info-color, #2196f3);
    padding: 12px 16px;
    border-radius: 4px;
    margin-top: 16px;
    font-size: 14px;
  }

  .unsaved-dialog {
    background: var(--card-background-color);
    border-radius: 8px;
    max-width: 400px;
    width: 90%;
    padding: 24px;
  }

  .unsaved-dialog h2 {
    margin: 0 0 12px 0;
    font-size: 20px;
    color: var(--warning-color, #ff9800);
  }

  .unsaved-dialog p {
    margin: 0 0 20px 0;
    color: var(--primary-text-color);
    line-height: 1.5;
  }

  .unsaved-dialog .action-buttons {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
    gap: 8px;
  }

  .btn-warning {
    background: var(--warning-color, #ff9800);
    color: white;
  }

  .btn-warning:hover {
    opacity: 0.9;
  }

  .btn-danger {
    background: transparent;
    color: var(--error-color, #f44336);
    border: 1px solid var(--error-color, #f44336);
  }

  .btn-danger:hover {
    background: rgba(244, 67, 54, 0.1);
  }

  .device-group {
    border: 1px solid var(--divider-color);
    border-radius: 8px;
    margin-bottom: 12px;
    overflow: hidden;
  }

  .device-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--secondary-background-color);
    cursor: pointer;
    user-select: none;
  }

  .device-header:hover {
    background: var(--divider-color);
  }

  .device-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }

  .expand-icon {
    width: 24px;
    height: 24px;
    transition: transform 0.2s;
    color: var(--secondary-text-color);
    flex-shrink: 0;
  }

  .expand-icon.expanded {
    transform: rotate(90deg);
  }

  .device-info {
    flex: 1;
    min-width: 0;
  }

  .device-name-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .device-name {
    font-weight: 500;
    color: var(--primary-text-color);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .device-meta {
    font-size: 12px;
    color: var(--secondary-text-color);
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .device-entities {
    padding: 0;
    border-top: 1px solid var(--divider-color);
  }

  .device-entities .entity-item {
    padding-left: 52px;
    background: var(--card-background-color);
  }

  .device-entities .entity-item:last-child {
    border-bottom: none;
  }

  .standalone-section {
    margin-top: 24px;
  }

  .standalone-section .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .standalone-icon {
    width: 20px;
    height: 20px;
    color: var(--secondary-text-color);
  }

  .search-results-info {
    color: var(--secondary-text-color);
    font-size: 14px;
    margin-bottom: 16px;
    padding: 8px 12px;
    background: var(--secondary-background-color);
    border-radius: 4px;
  }

  .no-results {
    text-align: center;
    padding: 32px;
    color: var(--secondary-text-color);
  }

  .edit-btn {
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color);
    cursor: pointer;
    font-size: 12px;
    color: var(--secondary-text-color);
    transition: all 0.2s;
  }

  .edit-btn:hover {
    background: var(--secondary-background-color);
    color: var(--primary-text-color);
  }

  .edit-btn.has-config {
    border-color: var(--primary-color);
    color: var(--primary-color);
  }

  .entity-config-dialog {
    background: var(--card-background-color);
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    padding: 24px;
  }

  .entity-config-dialog h2 {
    margin: 0 0 8px 0;
    font-size: 20px;
  }

  .entity-config-dialog .entity-id-subtitle {
    font-size: 12px;
    color: var(--secondary-text-color);
    margin-bottom: 20px;
    font-family: monospace;
  }

  .form-field {
    margin-bottom: 16px;
  }

  .form-field label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 6px;
    color: var(--primary-text-color);
  }

  .form-field .hint {
    font-size: 12px;
    color: var(--secondary-text-color);
    margin-top: 4px;
  }

  .form-field input[type="text"] {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--divider-color);
    border-radius: 4px;
    font-size: 14px;
    background: var(--card-background-color);
    color: var(--primary-text-color);
    box-sizing: border-box;
  }

  .form-field input:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  .alias-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }

  .alias-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: var(--primary-color);
    color: white;
    border-radius: 12px;
    font-size: 13px;
  }

  .alias-tag button {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 0;
    font-size: 14px;
    line-height: 1;
    opacity: 0.8;
  }

  .alias-tag button:hover {
    opacity: 1;
  }

  .add-alias-row {
    display: flex;
    gap: 8px;
  }

  .add-alias-row input {
    flex: 1;
  }

  .add-alias-row button {
    padding: 10px 16px;
    border: 1px solid var(--primary-color);
    background: var(--primary-color);
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }

  .add-alias-row button:hover {
    opacity: 0.9;
  }

  .suggest-btn {
    padding: 6px 12px;
    border: 1px dashed var(--primary-color);
    background: transparent;
    color: var(--primary-color);
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    margin-bottom: 8px;
  }

  .suggest-btn:hover {
    background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.1);
  }

  .alias-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
    padding: 8px;
    background: var(--secondary-background-color);
    border-radius: 4px;
  }

  .suggestion-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: var(--card-background-color);
    border: 1px solid var(--divider-color);
    border-radius: 12px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .suggestion-chip:hover {
    border-color: var(--primary-color);
    background: rgba(var(--rgb-primary-color, 33, 150, 243), 0.1);
  }

  .suggestion-chip .add-icon {
    color: var(--success-color, #4caf50);
    font-weight: bold;
  }

  .suggestions-label {
    font-size: 12px;
    color: var(--secondary-text-color);
    margin-bottom: 6px;
    display: block;
  }

  .config-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 6px;
    background: rgba(33, 150, 243, 0.15);
    color: var(--info-color, #2196f3);
    border-radius: 4px;
    font-size: 11px;
    margin-left: 8px;
  }

  /* Hide/show functionality */
  .search-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }

  .search-row .search-box {
    flex: 1;
    margin-bottom: 0;
  }

  .show-filtered-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--secondary-text-color);
    white-space: nowrap;
    cursor: pointer;
  }

  .show-filtered-toggle input {
    width: 16px;
    height: 16px;
  }

  .filter-btn {
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color);
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    opacity: 0.7;
  }

  .filter-btn:hover {
    opacity: 1;
    background: var(--secondary-background-color);
    border-color: var(--warning-color, #ff9800);
  }

  .filter-btn.is-filtered {
    opacity: 1;
    border-color: var(--warning-color, #ff9800);
    color: var(--warning-color, #ff9800);
    background: rgba(255, 152, 0, 0.1);
  }

  .filtered-item {
    opacity: 0.5;
    background: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 10px,
      rgba(0, 0, 0, 0.03) 10px,
      rgba(0, 0, 0, 0.03) 20px
    );
  }

  .filtered-item .device-header {
    background: rgba(0, 0, 0, 0.05);
  }

  /* Preview dialog enhancements */
  .changes-section {
    background: rgba(33, 150, 243, 0.1);
    border: 1px solid var(--info-color, #2196f3);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
  }

  .changes-title {
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--info-color, #2196f3);
  }

  .changes-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 200px;
    overflow-y: auto;
  }

  .change-entity {
    background: var(--card-background-color);
    padding: 8px 12px;
    border-radius: 4px;
    border-left: 3px solid var(--info-color, #2196f3);
  }

  .change-entity-id {
    font-family: monospace;
    font-size: 13px;
    color: var(--primary-text-color);
    display: block;
    margin-bottom: 4px;
  }

  .change-details {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .change-item {
    font-size: 12px;
    color: var(--secondary-text-color);
  }

  .change-old {
    color: var(--error-color, #f44336);
    text-decoration: line-through;
    margin-right: 4px;
  }

  .change-new {
    color: var(--success-color, #4caf50);
  }

  .config-summary {
    margin-left: 8px;
    font-weight: normal;
  }

  .preview-badge {
    font-size: 11px;
    padding: 2px 6px;
    background: var(--secondary-background-color);
    border-radius: 10px;
    margin-left: 4px;
  }

  .exposed-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .exposed-entity {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 8px;
    padding: 4px 8px;
    border-radius: 4px;
  }

  .exposed-entity.has-config {
    background: rgba(33, 150, 243, 0.05);
  }

  .exposed-entity .entity-id {
    font-family: monospace;
    font-size: 13px;
    color: var(--primary-text-color);
  }

  .exposed-entity .entity-detail {
    font-size: 11px;
    color: var(--secondary-text-color);
    background: var(--secondary-background-color);
    padding: 2px 6px;
    border-radius: 10px;
  }
`;
