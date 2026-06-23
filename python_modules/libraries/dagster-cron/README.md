# dagster-cron

Rust-backed cron schedule iteration for Dagster.

This package intentionally exposes a small surface area: native schedule construction,
forward/reverse iteration, `includes`, and Dagster-compatible helpers used by
`dagster._utils.schedules`.

The runtime package is not a croniter compatibility layer. Compatibility shims live only in tests.
