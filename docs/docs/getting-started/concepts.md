---
title: "Concepts"
sidebar_position: 200
---

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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
    Job ==> Definitions

    Partition ==> Asset
    IoManager ==> Asset

    Resource ==> Asset
    Resource ==> Schedule
    Resource ==> Sensor

    AssetCheck ==> Definitions
    AssetCheck ==> Asset

    Config ==> Schedule
    Config ==> Sensor
    Config ==> Job
    Config ==> Asset

    Asset ==> Job
    Asset ==> Schedule
    Asset ==> Sensor

    Asset ==> Definitions
    Schedule ==> Definitions
    Sensor ==> Definitions
    IoManager ==> Definitions
    Resource ==> Definitions

    Definitions ==> CodeLocation
```

Dagster provides a variety of abstractions for building and orchestrating data pipelines. These concepts enable a modular, declarative approach to data engineering, making it easier to manage dependencies, monitor execution, and ensure data quality.

### Asset

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

An `asset` represents a logical unit of data such as a table, dataset, or machine learning model. Assets can have dependencies on other assets, forming the data lineage for your pipelines. As the core abstraction in Dagster, assets can interact with many other Dagster concepts to facilitate certain tasks.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset check](concepts#asset-check) | `asset` may use an `asset check` | No |
| [config](concepts#config) | `asset` may use a `config` | No |
| [io manager](concepts#io-manager) | `asset` may use a `io manager` | No |
| [partition](concepts#partition) | `asset` may use a `partition` | No |
| [resource](concepts#resource) | `asset` may use a `resource` | No |
| [job](concepts#job) | `asset` may be used in a `job` | No |
| [schedule](concepts#schedule) | `asset` may be used in a `schedule` | No |
| [sensor](concepts#sensor) | `asset` may be used in a `sensor` | No |
| [definitions](concepts#definitions) | `asset` must be set in a `definitions` to be deployed | Yes |

### Asset Check

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

An `asset check` is associated with an `asset` to ensure it meets certain expectations around data quality, freshness or completeness. Asset checks run when the asset is executed and store metadata about the related run and if all the conditions of the check were met.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `asset check` may be used by an `asset` | No |
| [definitions](concepts#definitions) | `asset check` must be set in a `definitions` to be deployed | Yes |

### Code Location

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
    }
  }
}%%
  graph LR
    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    CodeLocation(Code Location)

    Definitions ==> CodeLocation
```

A `code location` is a collection of `definitions` deployed in a specific environment. A code location determines the Python environment (including the version of Dagster being used as well as any other Python dependencies). A Dagster project can have multiple code locations, helping isolate dependencies.

| Concept | Relationship | Required |
| --- | --- | --- |
| [definitions](concepts#definitions) | `code location` must contain at least one `definitions` | Yes |

### Config

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `config` is a set schema applied to a Dagster object that is input at the time of execution. This allows for parameterization and the reuse of pipelines to serve multiple purposes.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `config` may be used by an `asset` | No |
| [job](concepts#job) | `config` may be used by a `job` | No |
| [schedule](concepts#schedule) | `config` may be used by a `schedule` | No |
| [sensor](concepts#sensor) | `config` may be used by a `sensor` | No |

### Definitions

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `definitions` is a top-level construct containing all the objects of a Dagster project, such as `assets`, `jobs` and `schedules`. Only objects included in the definitions will be deployed and visible within the Dagster UI.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `definitions` may contain one or more `assets` | No |
| [asset check](concepts#asset-check) | `definitions` may contain one or more `asset checks` | No |
| [io manager](concepts#io-manager) | `definitions` may contain one or more `io managers` | No |
| [job](concepts#job) | `definitions` may contain one or more `jobs` | No |
| [resource](concepts#resource) | `definitions` may contain one or more `resources` | No |
| [schedule](concepts#schedule) | `definitions` may contain one or more `schedules` | No |
| [sensor](concepts#sensor) | `definitions` may contain one or more `sensors` | No |
| [code location](concepts#code-location) | `definitions` must be deployed in a `code location` | Yes |

### Graph

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `graph` connects multiple `ops` together to form a DAG. If you are using `assets`, you will not need to use graphs.

| Concept | Relationship | Required |
| --- | --- | --- |
| [config](concepts#config) | `graph` may use a `config` | No |
| [op](concepts#op) | `graph` must include one or more `ops` | Yes |
| [job](concepts#job) | `graph` must be part of `job` to execute | Yes |

### IO Manager

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
    }
  }
}%%
  graph LR
    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    IOManager(IO Manager)

    style Definitions fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    IOManager --> Asset
    IOManager ==> Definitions
```

An `io manager` defines how data is stored and retrieved between the execution of `assets` and `ops`. This allows for a customizable storage and format at any interaction in a pipeline.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `io manager` may be used by an `asset` | No |
| [definitions](concepts#definitions) | `io manager` must be set in a `definitions` to be deployed | Yes |

### Job

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `job` is a subset of `assets` or the `graph` of `ops`. Jobs are the main form of execution in Dagster.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `job` may contain a selection of `assets` | No |
| [config](concepts#config) | `job` may contain use `config` | No |
| [graph](concepts#graph) | `job` may contain a `graph` | No |
| [schedule](concepts#schedule) | `job` may be used by a `schedule` | No |
| [sensor](concepts#sensor) | `job` may be used by a `sensor` | No |
| [definitions](concepts#definitions) | `job` must be set in a `definitions` to be deployed | Yes |

### Op

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

An `op` is a computational unit of work. Ops are arranged into a `graph` to dictate their order. Ops have largely been replaced by `assets`.

| Concept | Relationship | Required |
| --- | --- | --- |
| [type](concepts#type) | `op` may use a `type` | No |
| [graph](concepts#type) | `op` must be contained in `graph` to execute | Yes |

### Partition

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
    }
  }
}%%
  graph LR
    Partition(Partition)

    style Asset fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Partition -.-> Asset
```

A `partition` represents a logical slice of a dataset or computation mapped to a certain segments (such as increments of time). Partitions enable incremental processing, making workflows more efficient by only running on relevant subsets of data.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `partition` may be used by an `asset` | No |

### Resource

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `resource` is a configurable external dependency. These can be databases, APIs, or anything outside of Dagster.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `resource` may be used by an `asset` | No |
| [schedule](concepts#schedule) | `resource` may be used by an `schedule` | No |
| [sensor](concepts#sensor) | `resource` may be used by an `sensor` | No |
| [definitions](concepts#definitions) | `resource` must be set in a `definitions` to be deployed | Yes |

### Type

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
    }
  }
}%%
  graph LR
    Type(Type)

    style Op fill:#BDBAB7,stroke:#BDBAB7,stroke-width:2px

    Type -.-> Op
```

A `type` is a way to define and validate the data passed between `ops`.

| Concept | Relationship | Required |
| --- | --- | --- |
| [op](concepts#op) | `type` may be used by an `op` | No |

### Schedule

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `schedule` is a way to automate `jobs` or `assets` to occur on a specified interval. In the cases that a job or asset is parameterized, the schedule can also be set with a run configuration (`config`) to match.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `schedule` may include a `job` or selection of `assets` | No |
| [config](concepts#config) | `schedule` may include a `config` if the `job` or `assets` include a `config` | No |
| [job](concepts#job) | `schedule` may include a `job` or selection of `assets` | No |
| [definitions](concepts#definitions) | `schedule` must be set in a `definitions` to be deployed | Yes |

### Sensor

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#4F43DD',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#231F1B',
      'lineColor': '#DEDDFF',
      'secondaryColor': '#BDBAB7',
      'tertiaryColor': '#BDBAB7'
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

A `sensor` is a way to trigger `jobs` or `assets` when an event occurs, such as a file being uploaded or a push notification. In the cases that a job or asset is parameterized, the sensor can also be set with a run configuration (`config`) to match.

| Concept | Relationship | Required |
| --- | --- | --- |
| [asset](concepts#asset) | `sensor` may include a `job` or selection of `assets` | No |
| [config](concepts#config) | `sensor` may include a `config` if the `job` or `assets` include a `config` | No |
| [job](concepts#job) | `sensor` may include a `job` or selection of `assets` | No |
| [definitions](concepts#definitions) | `sensor` must be set in a `definitions` to be deployed | Yes |
