# Agents

Machine monitoring collector — cross-platform JSON telemetry on an interval.

## Start here

1. Read [CURSOR.md](CURSOR.md) for architecture and extension rules.
2. Read [README.md](README.md) for user-facing behavior and configuration.
3. Use project skill `.cursor/skills/add-data-collector/` when adding metrics.

## Commands

```bash
python run.py              # uses config/config.json
python -m collector        # equivalent module entry
```

## Do not

- Add third-party packages without user approval (stdlib-only project).
- Add tests unless requested.
- Create or require a virtual environment.
- Collapse layers (keep `ICollector` vs `IPlatformProvider` separate).

## Extension point

New metrics → new `ICollector` + provider methods + `CollectorRegistry.register()`.
