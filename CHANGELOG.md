# Changelog

All notable changes to Django Mercury will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.8] - 2025-08-24

### Added
- **Plugin System Architecture** - Introduced modular plugin system with "small core, big plugin" design
  - Base `MercuryPlugin` class for creating custom plugins
  - Plugin priority system for execution order
  - Plugin lifecycle hooks (pre/post test, discovery enhancement)
  - Dynamic plugin loading from configuration

- **Profile-Based Configuration** - Three audience profiles with automatic plugin selection
  - `--profile student`: Educational mode with all learning plugins enabled
  - `--profile expert`: Minimal plugins for fast, efficient testing
  - `--profile agent`: Non-interactive mode with structured JSON output

- **Core Plugins**
  - **Discovery Plugin** (priority: 10) - Smart Django project finding with caching
  - **Wizard Plugin** (priority: 20) - Interactive test selection for beginners
  - **Learn Plugin** (priority: 60) - Interactive tutorials, quizzes, and progress tracking
  - **Hints Plugin** (priority: 90) - Performance tips based on test results

- **Configuration System**
  - TOML-based configuration with `mercury_config.toml`
  - Profile templates for different user types
  - Plugin-specific configuration sections
  - Environment-aware settings

- **Educational Features**
  - Interactive slideshow tutorials
  - Quiz system with progress tracking
  - Real-time performance explanations
  - Learning path recommendations
  - Gamification elements (achievements, XP)

- **CLI Enhancements**
  - `mercury-test` command replaces `python manage.py test`
  - Choose your profile: `--profile student`, `--profile expert`, or `--profile agent`
  - `--list-plugins` to view available plugins and their configuration
  - `--wizard` for guided test selection
  - `--learn` for educational mode
  - `--search-deep` for comprehensive project discovery
  - See [Plugin System Wiki](https://github.com/80-20-Human-In-The-Loop/Django-Mercury-Performance-Testing/wiki/Why-Plugins) for configuration details

### Changed
- Restructured codebase to support plugin architecture
- Enhanced reporting to adapt based on profile (educational vs concise vs JSON)
- Improved error messages with profile-aware guidance

### Documentation
- Created comprehensive wiki documentation
  - Quick Start Guide
  - Educational Mode Guide
  - Plugin System Documentation (Why Plugins, Student/Expert/Agent Plugins)
  - Understanding Reports
  - Workflow Best Practices

---

*Django Mercury follows the 80-20 Human-in-the-Loop philosophy: 80% automation, 20% human intelligence.*