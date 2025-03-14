---
title: 'Releases'
sidebar_position: 30
---

# Releases and compatibility

We follow [semantic versioning](https://semver.org/) for compatibility between Dagster releases.

## Dagster core

Dagster's public, stable APIs won't break within any major release. For example, if a public, stable API exists in Dagster 1.x.y, upgrading to 1.(x+1).y or 1.x.(y+1) shouldn't result in broken code.

:::tip
If a version breaks your code, help us out by filing an issue on [GitHub](https://github.com/dagster-io/dagster/issues).
:::

Our public, stable Python API includes:

- All classes, functions, and variables that are exported at the top-level of the `dagster` package, unless they're marked as [preview](#preview-apis) or [beta](#beta-apis).
- Public, non-[preview](#preview-apis) and non-[beta](#beta-apis) methods and properties of public, stable classes. Public methods and properties are those included in the [API reference](/api). Within the codebase, they're marked with a `@public` decorator.

### Preview APIs

The `Preview` marker allows us to offer new APIs to users and rapidly iterate based on their feedback. Preview APIs are marked as such in the [API reference](/api) and usually raise a `PreviewWarning` when used.

Preview APIs may have breaking changes in patch version releases. These features are not considered ready for production use.

### Beta APIs

The `Beta` marker allows us to offer new APIs to users and rapidly iterate based on their feedback. Beta APIs are marked as such in the [API reference](/api) and usually raise a `BetaWarning` when used.

Beta APIs may have breaking changes in minor version releases, with behavior changes in patch releases, but we try to avoid breaking them within minor releases if they have been around for a long time.

### Superseded APIs

The `Superseded` marker indicates that an API is still available, but is no longer the best practice. Usually, a better alternative is available. Superseded APIs are marked as such in the [API reference](/api) and usually raise a `SupersessionWarning` when used.

Like non-deprecated public stable APIs, superseded public stable APIs won't break within any major release after 1.0.

### Deprecated APIs

The `Deprecated` marker indicates that we recommend avoiding an API, because it will be removed in the future.

Like non-deprecated public stable APIs, deprecated public stable APIs won't break within any major release after 1.0.

## Dagster integration libraries

Dagster's integration libraries haven't yet achieved the same API maturity as Dagster core. For this reason, integration libraries remain on a pre-1.0 versioning track (in general 0.y.z of [semantic versioning](https://semver.org/) and 0.16+ as of Dagster 1.0.0) for the time being. However, 0.16+ library releases remain fully compatible with Dagster 1.x. We will graduate integration libraries one-by-one to the 1.x versioning track as they achieve API maturity.

While technically the 0.y.z phase of semantic versioning is "anything goes", we're conservative about making changes and will provide guidance about when to expect breaking changes:

- Upgrading to a new dot version within a minor release, such as 0.8.1 to 0.8.2, should never result in broken code. An exception to this guarantee is [preview](#preview-apis) and [beta](#beta-apis).
- As often as possible, deprecation warnings will precede removals. For example, if the current version is 0.8.5 and we want to remove an API, we'll issue a deprecation [warning](https://docs.python.org/3/library/warnings.html) when the API is used and remove it from 0.9.0.
- Upgrading to a new minor version, such as 0.7.5 to 0.8.0, may result in breakages or new deprecation [warnings](https://docs.python.org/3/library/warnings.html).

## Python version support

Each Dagster release strives to support the currently active versions of Python.

When a new version of Python is released, Dagster will work to add support once Dagster's own core dependencies have been updated to support it. **Note**: Some external libraries may not always be compatible with the latest version of Python.

When a version of Python reaches end of life, Dagster will drop support for it at the next convenient non-patch release.

## Changelog

The best way to stay on top of what changes are included in each release is through the [Dagster repository's changelog](https://github.com/dagster-io/dagster/blob/master/CHANGES.md). We call out breaking changes and deprecations in the **Breaking Changes** and **Deprecations** sections.
