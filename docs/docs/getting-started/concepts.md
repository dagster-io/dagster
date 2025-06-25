---
description: Dagster offers abstractions for data pipeline orchestration, enabling a modular, declarative approach to data engineering, making it easier to manage dependencies, monitor execution, and ensure data quality.
sidebar_position: 200
title: Concepts
---

Dagster provides a variety of abstractions for building and orchestrating data pipelines. These concepts enable a modular, declarative approach to data engineering, making it easier to manage dependencies, monitor execution, and ensure data quality.

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph TD

    AssetCheck(AssetCheck)
    %% click AssetCheck href "concepts#asset-check"

    Asset(Asset)
    %%click Asset href "concepts#asset"

    Config(Config)
    %%click Config href "concepts#config"

    CodeLocation(Code Location)
    %%click CodeLocation href "concepts#code-location"

    Definitions(Definitions)
    %%click Definitions href "concepts#definitions"

    Graph(Graph)
    %%click Graph href "concepts#graph"

    IoManager(IO Manager)
    %%click IoManager href "concepts#io-manager"

    Job(Job)
    %%click Job href "concepts#job"

    Op(Op)
    %%click Op href "concepts#op"

    Partition(Partition)
    %%click Partition href "concepts#partition"

    Resource(Resource)
    %%click Resource href "concepts#resource"

    Schedule(Schedule)
    %%click Schedule href "concepts#schedule"

    Sensor(Sensor)
    %%click Sensor href "concepts#sensor"

    Type(Type)
    %%click Type href "concepts#type"

    Type ==> Op
    Op ==> Graph
    Graph ==> Job

    Job ==> Schedule
    Job ==> Sensor
    Job ==> Component

    Partition ==> Asset
    IoManager ==> Asset

    Resource ==> Asset
    Resource ==> Schedule
    Resource ==> Sensor

    AssetCheck ==> Component
    AssetCheck ==> Asset

    Config ==> Schedule
    Config ==> Sensor
    Config ==> Job
    Config ==> Asset

    Asset ==> Job
    Asset ==> Schedule
    Asset ==> Sensor

    subgraph Component
    Definitions
    end

    Asset ==> Component
    Schedule ==> Component
    Sensor ==> Component
    IoManager ==> Component
    Resource ==> Component

    Component ==> CodeLocation
```

### Asset

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Config fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Partition fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Schedule fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Sensor fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style IOManager fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Resource fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style AssetCheck fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    AssetCheck -.-> Asset
    Config -.-> Asset
    Partition -.-> Asset
    Resource -.-> Asset
    IOManager -.-> Asset

    Asset(Asset)

    Asset -.-> Job
    Asset -.-> Schedule
    Asset -.-> Sensor
    Asset ==> Definitions
```

An <PyObject section="assets" module="dagster" object="asset" /> represents a logical unit of data such as a table, dataset, or machine learning model. Assets can have dependencies on other assets, forming the data lineage for your pipelines. As the core abstraction in Dagster, assets can interact with many other Dagster concepts to facilitate certain tasks. When you define an asset, either with the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator or via a <PyObject section="components" module="dagster" object="component" />, the definition is automatically added to a <PyObject section="definitions" module="dagster" object="Definitions" /> object.

| Concept                     | Relationship                                              |
| --------------------------- | --------------------------------------------------------- |
| [asset check](#asset-check) | `asset` may use an `asset check`                          |
| [asset spec](#asset-spec)   | `asset` is described by an `asset spec`                   |
| [component](#component)     | `asset` may be programmatically built by a component      |
| [config](#config)           | `asset` may use a `config`                                |
| [definitions](#definitions) | `asset` is added to a `Definitions` object to be deployed |
| [io manager](#io-manager)   | `asset` may use a `io manager`                            |
| [partition](#partition)     | `asset` may use a `partition`                             |
| [resource](#resource)       | `asset` may use a `resource`                              |
| [job](#job)                 | `asset` may be used in a `job`                            |
| [schedule](#schedule)       | `asset` may be used in a `schedule`                       |
| [sensor](#sensor)           | `asset` may be used in a `sensor`                         |

### Asset check

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    AssetCheck(Asset Check)

    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    AssetCheck -.-> Asset
    AssetCheck ==> Definitions
```

An <PyObject section="asset-checks" module="dagster" object="asset_check" /> is associated with an <PyObject section="assets" module="dagster" object="asset" /> to ensure it meets certain expectations around data quality, freshness or completeness. Asset checks run when the asset is executed and store metadata about the related run and if all the conditions of the check were met.

| Concept                     | Relationship                                                    |
| --------------------------- | --------------------------------------------------------------- |
| [asset](#asset)             | `asset check` may be used by an `asset`                         |
| [definitions](#definitions) | `asset check` is added to a `Definitions` object to be deployed |

### Asset spec

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    AssetSpec(Asset Spec)

    AssetSpec -.-> Asset
```

Specs are standalone objects that describe the identity and metadata of Dagster entities without defining their behavior. For example, an <PyObject module="dagster" section="assets" object="AssetSpec" /> contains essential information like the asset's <PyObject module="dagster" section="assets" object="AssetKey" displayText="key" /> (its unique identifier) and [tags](/guides/build/assets/metadata-and-tags) (labels for organizing and annotating the asset), but it doesn't include the logic for materializing that asset.

| Concept          | Relationship                                                |
| ---------------- | ----------------------------------------------------------- |
| [asset](s#asset) | `asset spec` may describe the identity and metadata `asset` |

### Code Location

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    CodeLocation(Code Location)

    Definitions ==> CodeLocation
```

A `code location` is a collection of <PyObject section="definitions" module="dagster" object="Definitions" /> deployed in a specific environment. A code location determines the Python environment (including the version of Dagster being used as well as any other Python dependencies). A Dagster project can have multiple code locations, helping isolate dependencies.

| Concept                     | Relationship                                                   |
| --------------------------- | -------------------------------------------------------------- |
| [definitions](#definitions) | `code location` must contain at least one `Definitions` object |

### Component

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    subgraph Component
    Definitions(Definitions)
    end
```

A `Component` is an opinionated project layout built around a <PyObject section="definitions" module="dagster" object="Definitions" /> object. The <PyObject section="definitions" module="dagster" object="Definitions" /> object contains Dagster objects used to accomplish a specific task, such as assets, asset checks, schedules, sensors, resources, and integrations. 

Components are objects that programmatically build assets and other definitions such as asset checks, schedules, resources, and sensors. They accept schematized configuration parameters (which are specified using YAML or lightweight Python) and use them to build the actual definitions you need. Components are designed to help you quickly bootstrap parts of your Dagster project and serve as templates for repeatable patterns.

| Concept                     | Relationship                                             |
| --------------------------- | -------------------------------------------------------- |
| [asset](#asset)             | `component` build `assets` and other `definitions`       |
| [asset check](#asset-check) | `component` build `asset_checks` and other `definitions` |
| [definitions](#definitions) | `component` build `assets` and other `definitions`       |
| [job](#job)                 | `component` build `jobs` and other `definitions`         |
| [schedule](#schedule)       | `component` build `schedules` and other `definitions`    |
| [sensor](#sensor)           | `component` build `sensors` and other `definitions`      |
| [resource](#resource)       | `component` build `resources` and other `definitions`    |
`

### Config

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    Config(Config)

    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Schedule fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Sensor fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Config -.-> Asset
    Config -.-> Job
    Config -.-> Schedule
    Config -.-> Sensor
```

A <PyObject section="config" module="dagster" object="RunConfig" /> is a set schema applied to a Dagster object that is input at the time of execution. This allows for parameterization and the reuse of pipelines to serve multiple purposes.

| Concept               | Relationship                         |
| --------------------- | ------------------------------------ |
| [asset](#asset)       | `config` may be used by an `asset`   |
| [job](#job)           | `config` may be used by a `job`      |
| [schedule](#schedule) | `config` may be used by a `schedule` |
| [sensor](#sensor)     | `config` may be used by a `sensor`   |

### Definitions

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Schedule fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Sensor fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style IOManager fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Resource fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style AssetCheck fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style CodeLocation fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px


    Asset -.-> Definitions
    AssetCheck -.-> Definitions
    IOManager -.-> Definitions
    Job -.-> Definitions
    Resource -.-> Definitions
    Schedule -.-> Definitions
    Sensor -.-> Definitions

    Definitions(Definitions)

    Definitions ==> CodeLocation
```

In Dagster, "definitions" means two things:
- The objects that combine metadata about Dagster entities with Python functions that define how they behave, for example, asset definitions, schedule definitions, and sensor definitions.
- The top-level `Definitions` object that contains references to all the definitions in a Dagster project, such as <PyObject section="assets" module="dagster" object="asset" />, <PyObject section="jobs" module="dagster" object="job" /> and <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> definitions. Entities included in the `Definitions` object will be deployed and visible within the Dagster UI.

| Concept                         | Relationship                                                                     |
| ------------------------------- | -------------------------------------------------------------------------------- |
| [asset](#asset)                 | Top-level `Definitions` object may contain one or more `asset` definitions       |
| [asset check](#asset-check)     | Top-level `Definitions` object may contain one or more `asset check` definitions |
| [io manager](#io-manager)       | Top-level `Definitions` object may contain one or more `io manager` definitions  |
| [job](#job)                     | Top-level `Definitions` object may contain one or more `job` definitions         |
| [resource](#resource)           | `definitions` may contain one or more `resource` definitions                     |
| [schedule](#schedule)           | `definitions` may contain one or more `schedule` definitions                     |
| [sensor](#sensor)               | `definitions` may contain one or more `sensors`                                  |
| [component](#component)         | `definitions` may exist as the output of a `component`                           |
| [code location](#code-location) | `definitions` must be deployed in a `code location`                              |

### Graph

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Config fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Op fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Graph(Graph)

    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Config -.-> Graph
    Op ==> Graph
    Graph ==> Job
```

A <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" /> connects multiple <PyObject section="ops" module="dagster" object="op" pluralize /> together to form a DAG. If you are using <PyObject section="assets" module="dagster" object="asset" pluralize />, you will not need to use graphs directly.

| Concept           | Relationship                             |
| ----------------- | ---------------------------------------- |
| [config](#config) | `graph` may use a `config`               |
| [op](#op)         | `graph` must include one or more `ops`   |
| [job](#job)       | `graph` must be part of `job` to execute |

### IO Manager

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    IOManager(IO Manager)

    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    IOManager -.-> Asset
    IOManager ==> Definitions
```

An <PyObject section="io-managers" module="dagster" object="IOManager" /> defines how data is stored and retrieved between the execution of <PyObject section="assets" module="dagster" object="asset" pluralize /> and <PyObject section="ops" module="dagster" object="op" pluralize />. This allows for a customizable storage and format at any interaction in a pipeline.

| Concept                     | Relationship                                               |
| --------------------------- | ---------------------------------------------------------- |
| [asset](#asset)             | `io manager` may be used by an `asset`                     |
| [definitions](#definitions) | `io manager` must be set in a `definitions` to be deployed |

### Job

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Graph fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Config fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Schedule fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Sensor fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Asset -.-> Job
    Config -.-> Job
    Graph -.-> Job

    Job(Job)

    Job -.-> Schedule
    Job -.-> Sensor
    Job ==> Definitions
```

A <PyObject section="jobs" module="dagster" object="job" /> is a subset of <PyObject section="assets" module="dagster" object="asset" pluralize /> or the <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" /> of <PyObject section="ops" module="dagster" object="op" pluralize />. Jobs are the main form of execution in Dagster.

| Concept                     | Relationship                                        |
| --------------------------- | --------------------------------------------------- |
| [asset](#asset)             | `job` may contain a selection of `assets`           |
| [config](#config)           | `job` may use a `config`                            |
| [graph](#graph)             | `job` may contain a `graph`                         |
| [schedule](#schedule)       | `job` may be used by a `schedule`                   |
| [sensor](#sensor)           | `job` may be used by a `sensor`                     |
| [definitions](#definitions) | `job` must be set in a `definitions` to be deployed |

### Op

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Type fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Op(Op)

    style Graph fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Type -.-> Op
    Op ==> Graph
```

An <PyObject section="ops" module="dagster" object="op" /> is a computational unit of work. Ops are arranged into a <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" /> to dictate their order. Ops have largely been replaced by <PyObject section="assets" module="dagster" object="asset" pluralize />.

| Concept         | Relationship                                 |
| --------------- | -------------------------------------------- |
| [type](#type)   | `op` may use a `type`                        |
| [graph](#graph) | `op` must be contained in `graph` to execute |

### Partition

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    Partition(Partition)

    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Partition -.-> Asset
```

A <PyObject section="partitions" object="PartitionsDefinition" /> represents a logical slice of a dataset or computation mapped to a certain segments (such as increments of time). Partitions enable incremental processing, making workflows more efficient by only running on relevant subsets of data.

| Concept         | Relationship                          |
| ----------------| ------------------------------------- |
| [asset](#asset) | `partition` may be used by an `asset` |

### Resource

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    Resource(Resource)

    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Schedule fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Sensor fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Resource -.-> Asset
    Resource -.-> Schedule
    Resource -.-> Sensor
    Resource ==> Definitions
```

A <PyObject section="resources" module="dagster" object="ConfigurableResource"/> is a configurable external dependency. These can be databases, APIs, or anything outside of Dagster.

| Concept                     | Relationship                                             |
| --------------------------- | -------------------------------------------------------- |
| [asset](#asset)             | `resource` may be used by an `asset`                     |
| [schedule](#schedule)       | `resource` may be used by a `schedule`                   |
| [sensor](#sensor)           | `resource` may be used by a `sensor`                     |
| [definitions](#definitions) | `resource` must be set in a `definitions` to be deployed |

### Type

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    Type(Type)

    style Op fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Type -.-> Op
```

A `type` is a way to define and validate the data passed between <PyObject section="ops" module="dagster" object="op" pluralize />.

| Concept   | Relationship                  |
| --------- | ----------------------------- |
| [op](#op) | `type` may be used by an `op` |

### Schedule

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Config fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Schedule(Schedule)

    Asset -.-> Schedule
    Config -.-> Schedule
    Job -.-> Schedule
    Schedule ==> Definitions
```

A <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> is a way to automate <PyObject section="jobs" module="dagster" object="job" pluralize /> or <PyObject section="assets" module="dagster" object="asset" pluralize /> to occur on a specified interval. In the cases that a job or asset is parameterized, the schedule can also be set with a run configuration (<PyObject section="config" module="dagster" object="RunConfig" />) to match.

| Concept                     | Relationship                                                                  |
| --------------------------- | ----------------------------------------------------------------------------- |
| [asset](#asset)             | `schedule` may include a `job` or selection of `assets`                       |
| [config](#config)           | `schedule` may include a `config` if the `job` or `assets` include a `config` |
| [job](#job)                 | `schedule` may include a `job` or selection of `assets`                       |
| [definitions](#definitions) | `schedule` must be set in a `definitions` to be deployed                      |

### Sensor

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#FFFFFF',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#FFFFFF'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Config fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px
    style Job fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Sensor(Sensor)

    Asset -.-> Sensor
    Config -.-> Sensor
    Job -.-> Sensor
    Sensor ==> Definitions
```

A `sensor` is a way to trigger <PyObject section="jobs" module="dagster" object="job" pluralize /> or <PyObject section="assets" module="dagster" object="asset" pluralize /> when an event occurs, such as a file being uploaded or a push notification. In the cases that a job or asset is parameterized, the sensor can also be set with a run configuration (<PyObject section="config" module="dagster" object="RunConfig" />) to match.

| Concept                     | Relationship                                                                |
| --------------------------- | --------------------------------------------------------------------------- |
| [asset](#asset)             | `sensor` may include a `job` or selection of `assets`                       |
| [config](#config)           | `sensor` may include a `config` if the `job` or `assets` include a `config` |
| [job](#job)                 | `sensor` may include a `job` or selection of `assets`                       |
| [definitions](#definitions) | `sensor` must be set in a `definitions` to be deployed                      |
