# CURSOR — Architecture and structure

This document is the primary reference for Cursor agents working in **ai-agent-monitoring-collector**. Read it before changing collection logic, providers, or configuration.

## Purpose

Collect machine telemetry on a schedule, persist as JSON, and remain easy to extend with new parameters across Windows, macOS, Linux, and ChromeOS.

## Layered architecture

```
┌─────────────────────────────────────────────────────────┐
│  Entry: run.py / python -m collector                    │
│  CollectorApplication (composition root)                  │
└──────────────────────────┬──────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   AppSettings      IntervalRunner    PlatformProviderFactory
         │                 │                 │
         │                 │                 ▼
         │                 │         IPlatformProvider
         │                 │         (windows|linux|darwin|chromeos)
         │                 │
         ▼                 ▼
  CollectorRegistry   CollectionOrchestrator
         │                 │
         ▼                 ▼
    ICollector(s) ──► MachineSnapshot ──► JsonSnapshotWriter
```

### Package map

| Path | Responsibility |
|------|----------------|
| `collector/app.py` | Wire dependencies, logging, run loop |
| `collector/config/settings.py` | Load and validate `config/config.json` |
| `collector/platform/detector.py` | Map host OS → `PlatformKind` |
| `collector/providers/` | OS-specific reads (single `IPlatformProvider` per host) |
| `collector/collectors/` | One `ICollector` per metric; mutates `MachineSnapshot` |
| `collector/collectors/registry.py` | Register and resolve collectors |
| `collector/services/orchestrator.py` | Run all collectors in one cycle |
| `collector/domain/models.py` | Immutable-ish value objects + `to_dict()` |
| `collector/storage/json_writer.py` | Write timestamped JSON + `latest.json` |
| `collector/scheduler/interval_runner.py` | Sleep loop between cycles |

## Key interfaces

### `IPlatformProvider` (`collector/providers/base.py`)

OS layer. Add methods here only when **all** platforms can expose the same concept, or use `extra` dict fields on domain models for platform-specific attributes.

### `ICollector` (`collector/collectors/base.py`)

Metric layer. One class per parameter group. Must implement:

- `name` — stable string matching `enabled_collectors` in config
- `collect(snapshot, provider)` — mutate `MachineSnapshot` in place

### `MachineSnapshot` (`collector/domain/models.py`)

Aggregate root for one cycle. Serialization via `to_dict()` for JSON output.

## Adding a new parameter (checklist)

1. Extend domain model if needed (`collector/domain/models.py`).
2. Add method to `IPlatformProvider` and implement on:
   - `windows_provider.py`
   - `linux_provider.py`
   - `darwin_provider.py`
   - `chromeos_provider.py` (subclass of Linux; override only when different)
3. Create `collector/collectors/your_metric.py` implementing `ICollector`.
4. Register in `build_default_registry()` in `registry.py`.
5. Document the collector `name` in README and config example.
6. Use skill `.cursor/skills/add-data-collector/SKILL.md` for consistent steps.

Prefer **new collector classes** over growing a god-class collector.

## Configuration contract

File: `config/config.json` (see `config.example.json`).

- `collection_interval_minutes` — must be &gt; 0 for continuous mode.
- `enabled_collectors` — `null` means all registered collectors; otherwise explicit list of `ICollector.name` values.

## Conventions for agents

- **Single responsibility** — Do not merge provider and collector logic.
- **No new dependencies** without explicit user approval; project uses stdlib only.
- **No tests** unless the user asks.
- **No virtualenv** — run with system `python`.
- **Cross-platform** — Every provider change must consider all four targets or document a deliberate limitation.
- **Errors** — Providers return `None` / empty collections; collectors do not crash the scheduler (orchestrator is wrapped by `IntervalRunner` try/except).
- **Output** — Never commit `data/` snapshots unless the user requests sample fixtures.

## Related Cursor assets

| Asset | Location |
|-------|----------|
| Agent summary | `AGENTS.md` |
| Architecture rule | `.cursor/rules/project-architecture.mdc` |
| Add collector skill | `.cursor/skills/add-data-collector/SKILL.md` |

## Running locally

```bash
python run.py
```

Set `"run_once": true` in config for a single cycle during development.
