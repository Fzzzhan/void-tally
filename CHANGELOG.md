# Changelog

All notable changes to VoidTally will be documented in this file.

## [0.2.0] - 2026-05-11

### Added
- **Email Notifications**: Daily void time reports via email
  - HTML-formatted email reports with session details
  - SMTP configuration with SSL/STARTTLS support
  - Automated scheduling with cron/Task Scheduler
  - Commands: `voidtally config email`, `voidtally send-report`, `voidtally schedule`
- **GitHub Pages**: Professional landing page at https://fzzzhan.github.io/void-tally/
  - Minimal terminal aesthetic with dark theme
  - Responsive design for all devices
  - Clear feature presentation
- **Session Deduplication**: Accurate statistics in dashboard and email reports
  - Auto-save sessions now update existing entries instead of creating duplicates
  - Email report totals match dashboard exactly

### Changed
- Improved SMTP connection handling for better email compatibility
- Enhanced dashboard and storage with deduplication support
- Updated README with simplified installation instructions

### Documentation
- Added EMAIL_NOTIFICATION.md with complete setup guide
- Updated README with email notification features
- Added MANIFEST.in and pyproject.toml for proper PyPI packaging

## [0.1.0] - 2026-05-10

### Added
- Initial release
- PTY proxy for non-intrusive monitoring
- Void time measurement and tracking
- Rich TUI dashboard with 7-day trends
- LOC tracking with snapshot attribution
- Project and tool filtering
- Local JSONL data storage
