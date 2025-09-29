<!--
Sync Impact Report
- Version change: Initial → 1.0.0
- New constitution for Python Rekordbox CSV Exporter project
- Added principles: Library-First, CLI Interface, Test-First, External Dependencies, Data Export Standards
- Added sections: Technology Standards, Development Workflow
- Templates requiring updates: ✅ plan-template.md (aligned), ✅ spec-template.md (aligned), ✅ tasks-template.md (aligned)
- Follow-up TODOs: None - all placeholders resolved
-->

# Python Rekordbox CSV Exporter Constitution

## Core Principles

### I. Library-First
Every feature starts as a standalone library with clear separation of concerns. Libraries must be self-contained, independently testable, and well-documented. The core Rekordbox interaction logic must be isolated from CLI interface code. No libraries exist solely for organizational purposes - each must solve a specific, testable problem.

### II. CLI Interface
Every library exposes functionality via a clean command-line interface. Follow text in/out protocol: arguments and stdin for input → structured output to stdout, errors to stderr. Support both JSON output for programmatic use and human-readable formats for interactive use. CLI must be intuitive for DJ workflow requirements.

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. All pyrekordbox integration points must have contract tests to verify data parsing correctness. User acceptance scenarios drive integration test design. No implementation without failing tests first.

### IV. External Dependencies
External dependencies must be justified and minimized. The pyrekordbox library is our core dependency - all interaction with Rekordbox data must go through this library's official API. Pin dependency versions explicitly. Create adapter layers for external libraries to enable testing and reduce coupling. Document dependency rationale in constitution violations if complexity increases.

### V. Data Export Standards
Data export operations must be reliable, predictable, and auditable. CSV exports must handle Unicode properly for international track names and artists. Provide data validation before export - warn users of missing or malformed data. Support incremental exports and duplicate detection. All data transformations must be transparent and documented.

## Technology Standards

Python 3.11+ required for modern typing and performance features. Use pytest for testing framework with clear test categories (unit, integration, contract). Follow PEP 8 style guidelines with automated formatting via black and ruff. Type hints mandatory for all public interfaces. Use click or typer for CLI framework to ensure consistent user experience.

## Development Workflow

All changes must pass constitution compliance checks before implementation. Contract tests must exist for pyrekordbox data access patterns and CSV export formats. Integration tests must cover complete user workflows: tag selection → song discovery → CSV generation. Performance requirements: Handle libraries with 10k+ tracks without memory issues. Error handling must be user-friendly with actionable messages for DJ users.

## Governance

This constitution supersedes all other development practices. Amendments require documentation of impact, justification, and migration plan. All implementation plans must verify compliance with these principles before proceeding to task generation phase.

All code reviews must verify compliance with core principles. Complexity increases must be justified against simpler alternatives. Constitution violations require explicit documentation in complexity tracking sections of implementation plans.

**Version**: 1.0.0 | **Ratified**: 2025-09-29 | **Last Amended**: 2025-09-29
