---
title: API lifecycle stages
---

This reference guide outlines the different stages in the lifecycle of Dagster APIs, from preview to deprecation. Understanding these stages helps developers make informed decisions about which APIs to use in their projects.

Dagster's API lifecycle is designed to balance innovation with stability, ensuring that developers can rely on consistent behavior while also benefiting from new features and improvements. This approach allows Dagster to evolve and adapt to changing requirements in the data engineering landscape while maintaining a stable foundation for existing projects.

The lifecycle stages described below provide a clear framework for understanding the maturity and reliability of different Dagster APIs. This transparency helps developers make informed decisions about which APIs to adopt in their projects, based on their specific needs for stability, feature completeness, and long-term support.

## API lifecycle stages

| Stage                    | Description                                                                                                | Lifetime                                                                                                            |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Preview                  | API in the design phase, can change significantly, or be removed completely. Not for production use.       | Until design is complete, or implementation cancelled                                                               |
| Beta                     | Features that is still being tested and may change. More stable than Preview, but still subject to change. | At most, two 1.x releases before it is either considered stable or returned to preview                              |
| Generally Available (GA) | Ready for production use, with minimal risk of breaking changes.                                           | Supported until at least 2.0                                                                                        |
| Superseded               | This API is still available, but is no longer the best practice. A better alternative is available.        | Supported until at least 2.0                                                                                        |
| Deprecated               | API is still available but will be removed in the future; avoid new usage.                                 | Will be removed in a minor release, the DeprecationWarning will indicate the next release that will remove the API. |

## Understanding the stages

### Preview

- **Purpose**: For early testing and feedback
- **Stability**: Highly unstable, expect frequent changes
- **Usage**: Not recommended for production environments
- **Documentation**: Minimal, typically just a README or unlisted documentation

### Beta

- **Purpose**: Feature testing with wider audience
- **Stability**: More stable than Preview, but still subject to changes
- **Usage**: Can be used in non-critical production environments
- **Documentation**: How-to guides and API documentation available

### GA (General Availability)

- **Purpose**: Production-ready features
- **Stability**: Stable with minimal risk of breaking changes
- **Usage**: Recommended for all production environments
- **Documentation**: Comprehensive documentation available

### Superseded

- **Purpose**: Maintains backwards compatibility while promoting newer alternatives
- **Stability**: Stable but no longer recommended
- **Usage**: Existing implementations can continue, but new projects should use the recommended alternative
- **Documentation**: API docs remain, but usage is discouraged in favor of newer alternatives

### Deprecated

- **Purpose**: Signals upcoming removal of the API
- **Stability**: Stable but scheduled for removal
- **Usage**: Existing implementations should plan migration
- **Documentation**: API docs remain, with clear warnings about deprecation. Arguments may be removed from function signature

### Dead

- **Purpose**: Removed APIs
- **Stability**: N/A
- **Usage**: No longer available for use
- **Documentation**: Removed from all documentation
