---
title: Dagster Embedded ELT (Deprecated)
sidebar_label: Embedded ELT (Deprecated)
description: dagster-embedded-elt has been deprecated and replaced by dagster-sling and dagster-dlt.
slug: /integrations/libraries/embedded-elt
canonicalUrl: '/integrations/libraries/embedded-elt'
---

`dagster-embedded-elt` and the `dagster_embedded_elt` package have been deprecated.

Use the replacement libraries instead:

- **Sling integration**: [`dagster-sling`](/integrations/libraries/sling)
- **dlt integration**: [`dagster-dlt`](/integrations/libraries/dlt)

If you're migrating existing code:

- Replace imports from `dagster_embedded_elt.sling` with `dagster_sling`
- Replace imports from `dagster_embedded_elt.dlt` with `dagster_dlt`
