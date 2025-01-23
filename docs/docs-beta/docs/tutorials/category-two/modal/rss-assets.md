---
title: RSS
description: Processing RSS feeds
last_update:
  author: Dennis Hume
sidebar_position: 20
---



<CodeExample path="project_dagster_modal_pipes/project_dagster_modal_pipes/pipeline_factory.py" language="python" lineStart="209" lineEnd="219"/>




sensor

using `etag` to only get new podcasts. Dagster will maintain cursor
- first time pull all podcasts
- next only look for new podcasts based on `etag`


## Next steps

- Continue this tutorial with []()