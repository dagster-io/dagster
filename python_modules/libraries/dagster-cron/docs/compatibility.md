# Cron Compatibility

`dagster-cron` targets Dagster's public cron schedule behavior, not croniter's full
private API surface.

Supported through the Dagster runtime path:

- Five-field cron expressions and lowercase aliases `@hourly`, `@daily`, `@weekly`, `@monthly`,
  and `@yearly`.
- Croniter-compatible aliases `@annually` and `@midnight`, normalized in Rust.
- Day-of-week Sunday values `0` and `7`.
- Named months and weekdays.
- `?` in day-of-month and day-of-week fields.
- `L`, nearest weekday `W`, and nth weekday `#` specifiers supported by the active cron crate
  branch.
- Forward and reverse iteration in named timezones.
- DST nonexistent-time handling with next-existent behavior.

Known unsupported or intentionally unsupported croniter surfaces:

- Hashed `H` expressions.
- `@reboot`.
- `expand_from_start_time`.
- `implement_cron_bug`.
- croniter private expanded-state/helper APIs.
- croniter's strict default 1970-2099 year-range reachability checks.
- croniter-specific behavior around some unions of special specifiers.

The copied croniter compatibility shim and parity tests in `tests/` are test-only. They must not be
imported by Dagster runtime code.
