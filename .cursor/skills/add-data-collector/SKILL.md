---
name: add-data-collector
description: >-
  Add a new machine telemetry collector to ai-agent-monitoring-collector.
  Use when extending metrics, adding parameters, or implementing ICollector.
---

# Add a data collector

Follow this workflow to add a new collected parameter while keeping single responsibility and cross-platform support.

## 1. Domain model

Edit `collector/domain/models.py`:

- Add fields to `MachineSnapshot`, or introduce a small `@dataclass` value object.
- Ensure `to_dict()` still serializes new fields (dataclass nesting is handled automatically).

## 2. Platform contract

Edit `collector/providers/base.py`:

- Add an abstract method on `IPlatformProvider` if every OS should expose the same data shape.

## 3. Platform implementations

Implement the method in **all** of:

- `collector/providers/windows_provider.py`
- `collector/providers/linux_provider.py`
- `collector/providers/darwin_provider.py`
- `collector/providers/chromeos_provider.py` (override only if ChromeOS differs from Linux)

Use `collector/providers/_command.py` for subprocess helpers and shared mixins in `_unix.py` when logic is identical on Linux and ChromeOS.

Return `None` or empty collections when data is unavailable — do not raise for missing optional telemetry.

## 4. Collector class

Create `collector/collectors/<metric_name>.py`:

```python
from collector.collectors.base import ICollector
from collector.domain.models import MachineSnapshot
from collector.providers.base import IPlatformProvider


class ExampleCollector(ICollector):
    @property
    def name(self) -> str:
        return "example_metric"  # matches config enabled_collectors

    def collect(self, snapshot: MachineSnapshot, provider: IPlatformProvider) -> None:
        snapshot.extra["example_metric"] = provider.get_example()  # or dedicated field
```

Prefer a dedicated `MachineSnapshot` field over `extra` when the metric is first-class.

## 5. Registry

In `collector/collectors/registry.py`, import the collector and call `registry.register(...)` inside `build_default_registry()`.

## 6. Documentation

- Add the collector name to `config/config.example.json` comments or README table.
- Mention platform caveats in README if tools require root/admin.

## 7. Verify

```bash
# config/config.json → "run_once": true
python run.py
```

Inspect `data/latest.json` for the new fields.

## Naming

- Collector `name`: snake_case, stable, used in `enabled_collectors`.
- One collector per logical parameter group (not one mega-collector).
