# Changelog

## 0.1.17

- `dg docs component-type ` now provides detailed information on component schema.
- `dg check definitions` is now available, which functions similarly to `dagster definitions validate`. When run at the project level, it will ensure all definitions load properly. When run at the workspace level, it will do so for all projects.

## 0.1.16

- The entire dg CLI has been changed from noun-first to verb-first, e.g. dg code-location scaffold is now dg scaffold code-location.
- Some commands have also been renamed beyond the switch in order:
  - The `info` command has been renamed to `inspect`. `dg component-type info` is now `dg inspect component-type`.
  - `dg component check` command is now `dg check yaml`.

## 0.1.15

_Inception of changelog occurs at this point_
