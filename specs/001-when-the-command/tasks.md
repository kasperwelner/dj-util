# Tasks: Rekordbox Streaming Tag Exporter

**Input**: Design documents from `/specs/001-when-the-command/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: Python 3.11+, pyrekordbox, click, pytest
2. Load design documents:
   → data-model.md: MyTag, Track, CSVExport, TagSelection → model tasks
   → contracts/cli-export.yaml: CLI command contract → CLI test task
   → research.md: Technical decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: Database adapter, CSV export
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Validate task completeness
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- All paths shown below are relative to repository root

## Phase 3.1: Setup
- [x] T001 Create project structure with src/models/, src/services/, src/cli/, src/lib/, tests/ directories
- [x] T002 Initialize Python project with setup.py and requirements.txt including pyrekordbox>=0.3.0, click>=8.0, pytest>=7.0
- [x] T003 [P] Configure .pre-commit-config.yaml with black, ruff, and mypy for code quality
- [x] T004 [P] Create pyproject.toml with project metadata and tool configurations

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T005 [P] Contract test for pyrekordbox database connection in tests/contract/test_rekordbox_contract.py
- [x] T006 [P] Contract test for CSV output format with Unicode in tests/contract/test_csv_format_contract.py
- [x] T007 [P] Integration test for interactive tag selection flow in tests/integration/test_tag_selection_flow.py
- [x] T008 [P] Integration test for complete export workflow in tests/integration/test_export_workflow.py
- [x] T009 [P] Integration test for error scenarios (no tags, no matches) in tests/integration/test_error_scenarios.py
- [x] T010 [P] CLI test for rekordbox-export command arguments in tests/cli/test_export_command.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T011 [P] MyTag model with id, name, track_count in src/models/tag.py
- [ ] T012 [P] Track model with id, artist, title, folder_path, is_streaming property in src/models/track.py
- [ ] T013 [P] CSVExport model with file validation and Unicode handling in src/models/csv_export.py
- [ ] T014 [P] TagSelection model for interactive selection state in src/models/tag_selection.py
- [ ] T015 [P] RekordboxAdapter service wrapping pyrekordbox in src/services/rekordbox.py
- [ ] T016 [P] TagSelector service with interactive checkbox UI in src/services/tag_selector.py
- [ ] T017 [P] CSVExporter service with DictWriter and UTF-8-sig in src/services/csv_exporter.py
- [ ] T018 [P] Validators for path and selection validation in src/lib/validators.py
- [ ] T019 Export command CLI implementation with click in src/cli/export_command.py
- [ ] T020 Main entry point connecting CLI to services in src/cli/__main__.py
- [ ] T021 [P] Progress feedback implementation for tag selection and export in src/lib/progress.py

## Phase 3.4: Integration
- [ ] T022 Connect RekordboxAdapter to actual database with error handling
- [ ] T023 Implement streaming track filtering (empty FolderPath check)
- [ ] T024 Implement MyTag filtering with ContentMyTag junction table
- [ ] T025 Integrate progress indicators with long operations
- [ ] T026 Add database auto-detection for macOS/Windows/Linux
- [ ] T027 Implement --limit flag for testing with subset

## Phase 3.5: Polish
- [ ] T028 [P] Unit tests for MyTag model in tests/unit/test_tag_model.py
- [ ] T029 [P] Unit tests for Track model and is_streaming in tests/unit/test_track_model.py
- [ ] T030 [P] Unit tests for validators in tests/unit/test_validators.py
- [ ] T031 [P] Unit tests for CSVExporter Unicode handling in tests/unit/test_csv_exporter.py
- [ ] T032 Performance test for 10k track filtering (<5 seconds)
- [ ] T033 Memory profiling for large exports (<500MB)
- [ ] T034 [P] Create README.md with installation and usage instructions
- [ ] T035 [P] Create docs/api.md with module documentation
- [ ] T036 Run quickstart.md validation scenarios

## Dependencies
- Setup (T001-T004) before all other tasks
- Tests (T005-T010) before implementation (T011-T020)
- Models (T011-T014) before services (T015-T018)
- Services before CLI integration (T019-T020)
- Core implementation before integration (T021-T026)
- Everything before polish (T027-T035)

## Parallel Execution Examples

### After Setup, Run All Tests Together:
```bash
# Launch T005-T010 in parallel (all different test files):
Task: "Contract test for pyrekordbox database connection in tests/contract/test_rekordbox_contract.py"
Task: "Contract test for CSV output format with Unicode in tests/contract/test_csv_format_contract.py"
Task: "Integration test for interactive tag selection flow in tests/integration/test_tag_selection_flow.py"
Task: "Integration test for complete export workflow in tests/integration/test_export_workflow.py"
Task: "Integration test for error scenarios in tests/integration/test_error_scenarios.py"
Task: "CLI test for rekordbox-export command arguments in tests/cli/test_export_command.py"
```

### After Tests Pass, Create All Models in Parallel:
```bash
# Launch T011-T014 together (independent model files):
Task: "MyTag model with id, name, track_count in src/models/tag.py"
Task: "Track model with id, artist, title, folder_path, is_streaming in src/models/track.py"
Task: "CSVExport model with file validation in src/models/csv_export.py"
Task: "TagSelection model for interactive selection in src/models/tag_selection.py"
```

### Create All Services in Parallel:
```bash
# Launch T015-T018 together (independent service files):
Task: "RekordboxAdapter service wrapping pyrekordbox in src/services/rekordbox.py"
Task: "TagSelector service with interactive checkbox UI in src/services/tag_selector.py"
Task: "CSVExporter service with DictWriter and UTF-8-sig in src/services/csv_exporter.py"
Task: "Validators for path and selection validation in src/lib/validators.py"
```

### Polish Phase Unit Tests in Parallel:
```bash
# Launch T028-T031 together (independent test files):
Task: "Unit tests for MyTag model in tests/unit/test_tag_model.py"
Task: "Unit tests for Track model and is_streaming in tests/unit/test_track_model.py"
Task: "Unit tests for validators in tests/unit/test_validators.py"
Task: "Unit tests for CSVExporter Unicode handling in tests/unit/test_csv_exporter.py"
```

## Notes
- **TDD Strict**: Tests MUST fail before implementation
- **Constitution Compliance**: Library-first architecture, test-first development
- **Unicode Critical**: All string handling must preserve Unicode (Japanese, emoji)
- **Database Read-Only**: Never modify Rekordbox database
- **CLI Focus**: Interactive experience is primary interface
- **Performance Target**: 10k tracks in <5 seconds, <500MB memory

## Task Generation Rules
*Applied during main() execution*

1. **From CLI Contract**:
   - cli-export.yaml → CLI test task (T010)
   - CLI options → implementation in export_command.py
   
2. **From Data Model**:
   - MyTag entity → tag.py model (T011)
   - Track entity → track.py model (T012)
   - CSVExport entity → csv_export.py model (T013)
   - TagSelection entity → tag_selection.py model (T014)
   
3. **From User Stories**:
   - Interactive tag selection → test_tag_selection_flow.py (T007)
   - Export workflow → test_export_workflow.py (T008)
   - Error scenarios → test_error_scenarios.py (T009)

4. **Ordering**:
   - Setup → Tests → Models → Services → CLI → Integration → Polish
   - Parallel execution for independent files only

## Validation Checklist
*GATE: Verified before task execution*

- [x] CLI contract has corresponding test (T010)
- [x] All entities have model tasks (T011-T014)
- [x] All tests come before implementation
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] Constitution principles enforced (Library-First, Test-First)