# Contributing to Google Home Exposure Manager

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/GoogleHomeExposureManager.git
   ```
3. Copy to your Home Assistant custom_components folder for testing:
   ```bash
   cp -r custom_components/google_home_exposure_manager /path/to/homeassistant/custom_components/
   ```

## Code Style

- Use `from __future__ import annotations` for forward references
- Use type hints for all function signatures
- Use module-level loggers (`_LOGGER = logging.getLogger(__name__)`)
- Follow PEP 8 conventions
- Run validation before committing:
  ```bash
  python -m py_compile custom_components/google_home_exposure_manager/*.py
  ```

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Make your changes
3. Ensure all validation passes (GitHub Actions will check this)
4. Update documentation if needed
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Translation Contributions

Translations help make this integration accessible to users worldwide. This project currently supports:
- English (en) - Source language
- French (fr)
- German (de)
- Spanish (es)
- Italian (it)
- Dutch (nl)

### Translation Files

- `strings.json` - Source of truth (English), copied to `translations/en.json`
- `translations/*.json` - Language-specific translations

### Adding or Updating Translations

1. **For English changes**: Edit `strings.json`, then copy to `translations/en.json`
2. **For other languages**: Edit the corresponding `translations/{lang}.json` file
3. **For new languages**: 
   - Copy `translations/en.json` to `translations/{lang}.json`
   - Translate all string values (do NOT translate keys)
   - Submit a PR

### Keeping Translations in Sync

When adding new strings to `strings.json`:

1. Add the new keys to `strings.json` and `translations/en.json`
2. Add the same keys to ALL translation files with English as placeholder
3. Consider using AI translation tools for initial translations, then mark for review
4. Translations can be community-reviewed in future PRs

**Important**: All translation files must have the same structure (same keys). Missing keys will cause the integration to fall back to English.

### Translation Review Process

- AI-generated translations are welcome as starting points
- Native speakers are encouraged to review and improve translations
- Mark reviewed translations by updating any relevant tracking comments

## Releasing New Versions

1. Update version in `manifest.json`
2. Update `CHANGELOG.md`
3. Create a GitHub release with tag format `vX.Y.Z`
4. The release workflow will automatically attach a zip file

---

## HACS Default Repository Listing

This section documents the requirements for getting this integration listed in the default HACS repository.

### Prerequisites for Default Listing

Before submitting to [hacs/default](https://github.com/hacs/default), ensure:

1. **GitHub Repository Requirements**
   - [ ] Repository has a description
   - [ ] Repository has topics (e.g., `home-assistant`, `hacs`, `google-assistant`, `google-home`)
   - [ ] Repository has issues enabled
   - [ ] Repository is not archived

2. **GitHub Actions Pass**
   - [ ] [HACS Action](https://github.com/hacs/action) passes without errors
   - [ ] [Hassfest](https://github.com/home-assistant/actions#hassfest) passes

3. **GitHub Release Exists**
   - [ ] At least one GitHub release (not just a tag) has been created

4. **Brands Repository (REQUIRED)**
   - [ ] Submit PR to [home-assistant/brands](https://github.com/home-assistant/brands)
   - This is **required** for integrations to be included in HACS defaults
   - See instructions below

### Submitting to home-assistant/brands

The [home-assistant/brands](https://github.com/home-assistant/brands) repository contains icons and logos for integrations. For custom integrations, you need to add an entry to get listed in HACS defaults.

1. Fork [home-assistant/brands](https://github.com/home-assistant/brands)

2. Create the following structure:
   ```
   custom_integrations/google_home_exposure_manager/
   ├── icon.png        # 256x256 PNG icon
   ├── icon@2x.png     # 512x512 PNG icon (optional, for retina)
   ├── logo.png        # Full logo (optional)
   └── logo@2x.png     # Retina logo (optional)
   ```

3. Add entry to `custom_integrations/google_home_exposure_manager/manifest.json`:
   ```json
   {
     "domain": "google_home_exposure_manager",
     "name": "Google Home Exposure Manager"
   }
   ```

4. Submit a PR to the brands repository

5. After the brands PR is merged, you can submit to hacs/default

### Submitting to hacs/default

1. Fork [hacs/default](https://github.com/hacs/default)
2. Create a new branch from `master`
3. Add the repository URL to the `integration` file in alphabetical order:
   ```
   NathanMagnus/GoogleHomeExposureManager
   ```
4. Submit a PR using the template
5. Wait for review (can take months due to backlog)

### References

- [HACS Publishing Docs](https://hacs.xyz/docs/publish/start)
- [Integration Requirements](https://hacs.xyz/docs/publish/integration)
- [Include Default Repositories](https://hacs.xyz/docs/publish/include)
- [home-assistant/brands](https://github.com/home-assistant/brands)
