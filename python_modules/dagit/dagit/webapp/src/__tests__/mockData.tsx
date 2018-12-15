import { APP_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { CONFIG_CODE_EDITOR_CONTAINER_QUERY } from "../configeditor/ConfigCodeEditorContainer";

const MOCKS = [
  {
    request: {
      operationName: "TypeListContainerQuery",
      queryVariableName: "TYPE_LIST_CONTAINER_QUERY",
      query: TYPE_LIST_CONTAINER_QUERY,
      variables: { pipelineName: "pandas_hello_world" }
    },
    result: {
      data: {
        pipelineOrError: {
          __typename: "Pipeline",
          types: [
            {
              name: "Bool",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "RegularType"
            },
            {
              name: "Dict.1",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "Dict.2",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "PandasDataFrame",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description:
                "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
              __typename: "RegularType"
            },
            {
              name: "PandasHelloWorld.ContextConfig",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ContextDefinitionConfig.Default",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name:
                "PandasHelloWorld.ContextDefinitionConfig.Default.Resources",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.Environment",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ExecutionConfig",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ExpectationsConfig",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SolidConfig.LoadNumCsv",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SolidsConfigDictionary",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Path",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "RegularType"
            },
            {
              name: "String",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "RegularType"
            }
          ]
        }
      }
    }
  },

  {
    request: {
      operationName: "ConfigCodeEditorContainerQuery",
      queryVariableName: "CONFIG_CODE_EDITOR_CONTAINER_QUERY",
      query: CONFIG_CODE_EDITOR_CONTAINER_QUERY,
      variables: { pipelineName: "pandas_hello_world" }
    },
    result: {
      data: {
        pipelineOrError: {
          __typename: "Pipeline",
          types: [
            { __typename: "RegularType", name: "Bool" },
            {
              __typename: "CompositeType",
              name: "Dict.1",
              fields: [
                {
                  name: "path",
                  type: { name: "Path", __typename: "RegularType" },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "Dict.2",
              fields: [
                {
                  name: "log_level",
                  type: { name: "String", __typename: "RegularType" },
                  __typename: "TypeField"
                }
              ]
            },
            { __typename: "RegularType", name: "PandasDataFrame" },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.ContextConfig",
              fields: [
                {
                  name: "default",
                  type: {
                    name: "PandasHelloWorld.ContextDefinitionConfig.Default",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.ContextDefinitionConfig.Default",
              fields: [
                {
                  name: "config",
                  type: { name: "Dict.2", __typename: "CompositeType" },
                  __typename: "TypeField"
                },
                {
                  name: "resources",
                  type: {
                    name:
                      "PandasHelloWorld.ContextDefinitionConfig.Default.Resources",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name:
                "PandasHelloWorld.ContextDefinitionConfig.Default.Resources",
              fields: []
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.Environment",
              fields: [
                {
                  name: "context",
                  type: {
                    name: "PandasHelloWorld.ContextConfig",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                },
                {
                  name: "solids",
                  type: {
                    name: "PandasHelloWorld.SolidsConfigDictionary",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                },
                {
                  name: "expectations",
                  type: {
                    name: "PandasHelloWorld.ExpectationsConfig",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                },
                {
                  name: "execution",
                  type: {
                    name: "PandasHelloWorld.ExecutionConfig",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.ExecutionConfig",
              fields: [
                {
                  name: "serialize_intermediates",
                  type: { name: "Bool", __typename: "RegularType" },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.ExpectationsConfig",
              fields: [
                {
                  name: "evaluate",
                  type: { name: "Bool", __typename: "RegularType" },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.SolidConfig.LoadNumCsv",
              fields: [
                {
                  name: "config",
                  type: { name: "Dict.1", __typename: "CompositeType" },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "PandasHelloWorld.SolidsConfigDictionary",
              fields: [
                {
                  name: "load_num_csv",
                  type: {
                    name: "PandasHelloWorld.SolidConfig.LoadNumCsv",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            { __typename: "RegularType", name: "Path" },
            { __typename: "RegularType", name: "String" }
          ]
        }
      }
    }
  },

  {
    request: {
      operationName: "TypeExplorerContainerQuery",
      queryVariableName: "TYPE_EXPLORER_CONTAINER_QUERY",
      query: TYPE_EXPLORER_CONTAINER_QUERY,
      variables: {
        pipelineName: "pandas_hello_world",
        typeName: "PandasDataFrame"
      }
    },
    result: {
      data: {
        type: {
          __typename: "RegularType",
          name: "PandasDataFrame",
          description:
            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
          typeAttributes: {
            isBuiltin: false,
            isSystemConfig: false,
            __typename: "TypeAttributes",
            isNamed: true
          }
        }
      }
    }
  },

  {
    request: {
      operationName: "PipelineseContainerQuery",
      queryVariableName: "APP_QUERY",
      query: APP_QUERY,
      variables: undefined
    },
    result: {
      data: {
        pipelinesOrError: {
          __typename: "PipelineConnection",
          nodes: [
            {
              name: "pandas_hello_world",
              runs: [
                {
                  runId: "d359c04d-8c4a-4851-ae62-bc24028e1468",
                  status: "SUCCESS",
                  logs: {
                    nodes: [
                      {
                        message:
                          "Beginning execution of pipeline pandas_hello_world",
                        timestamp: "1544860601216",
                        level: "INFO",
                        __typename: "PipelineStartEvent"
                      },
                      {
                        message:
                          "About to execute the compute node graph in the following order ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544860601218",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Entering execute_steps loop. Order: ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544860601220",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Beginning execution of load_num_csv.transform",
                        timestamp: "1544860601221",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid load_num_csv.",
                        timestamp: "1544860601221",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid load_num_csv emitted output "result" value    num1  num2\n0     1     2\n1     3     4',
                        timestamp: "1544860601301",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of load_num_csv.transform succeeded in 80.23190498352051",
                        timestamp: "1544860601302",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message: "Beginning execution of sum_solid.transform",
                        timestamp: "1544860601303",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid sum_solid.",
                        timestamp: "1544860601303",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid sum_solid emitted output "result" value    num1  num2  sum\n0     1     2    3\n1     3     4    7',
                        timestamp: "1544860601318",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of sum_solid.transform succeeded in 15.486955642700195",
                        timestamp: "1544860601319",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Beginning execution of sum_sq_solid.transform",
                        timestamp: "1544860601321",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid sum_sq_solid.",
                        timestamp: "1544860601321",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid sum_sq_solid emitted output "result" value    num1  num2  sum  sum_sq\n0     1     2    3       9\n1     3     4    7      49',
                        timestamp: "1544860601330",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of sum_sq_solid.transform succeeded in 9.60993766784668",
                        timestamp: "1544860601331",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Completing successful execution of pipeline pandas_hello_world",
                        timestamp: "1544860601332",
                        level: "INFO",
                        __typename: "PipelineSuccessEvent"
                      }
                    ],
                    __typename: "LogMessageConnection",
                    pageInfo: { lastCursor: "15", __typename: "PageInfo" }
                  },
                  executionPlan: {
                    steps: [
                      {
                        name: "load_num_csv.transform",
                        solid: { name: "load_num_csv", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_solid.transform",
                        solid: { name: "sum_solid", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_sq_solid.transform",
                        solid: { name: "sum_sq_solid", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      }
                    ],
                    __typename: "ExecutionPlan"
                  },
                  __typename: "PipelineRun"
                },
                {
                  runId: "1cf3859c-2e71-4448-8db6-176aca626cc8",
                  status: "SUCCESS",
                  logs: {
                    nodes: [
                      {
                        message:
                          "Beginning execution of pipeline pandas_hello_world",
                        timestamp: "1544860606343",
                        level: "INFO",
                        __typename: "PipelineStartEvent"
                      },
                      {
                        message:
                          "About to execute the compute node graph in the following order ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544860606345",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Entering execute_steps loop. Order: ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544860606348",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Beginning execution of load_num_csv.transform",
                        timestamp: "1544860606350",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid load_num_csv.",
                        timestamp: "1544860606351",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid load_num_csv emitted output "result" value    num1  num2\n0     1     2\n1     3     4',
                        timestamp: "1544860606396",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of load_num_csv.transform succeeded in 46.205997467041016",
                        timestamp: "1544860606398",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message: "Beginning execution of sum_solid.transform",
                        timestamp: "1544860606399",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid sum_solid.",
                        timestamp: "1544860606399",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid sum_solid emitted output "result" value    num1  num2  sum\n0     1     2    3\n1     3     4    7',
                        timestamp: "1544860606415",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of sum_solid.transform succeeded in 15.848875045776367",
                        timestamp: "1544860606416",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Beginning execution of sum_sq_solid.transform",
                        timestamp: "1544860606417",
                        level: "INFO",
                        __typename: "ExecutionStepStartEvent",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Executing core transform for solid sum_sq_solid.",
                        timestamp: "1544860606417",
                        level: "DEBUG",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          'Solid sum_sq_solid emitted output "result" value    num1  num2  sum  sum_sq\n0     1     2    3       9\n1     3     4    7      49',
                        timestamp: "1544860606429",
                        level: "INFO",
                        __typename: "LogMessageEvent"
                      },
                      {
                        message:
                          "Execution of sum_sq_solid.transform succeeded in 12.370824813842773",
                        timestamp: "1544860606430",
                        level: "INFO",
                        __typename: "ExecutionStepSuccessEvent",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        message:
                          "Completing successful execution of pipeline pandas_hello_world",
                        timestamp: "1544860606430",
                        level: "INFO",
                        __typename: "PipelineSuccessEvent"
                      }
                    ],
                    __typename: "LogMessageConnection",
                    pageInfo: { lastCursor: "15", __typename: "PageInfo" }
                  },
                  executionPlan: {
                    steps: [
                      {
                        name: "load_num_csv.transform",
                        solid: { name: "load_num_csv", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_solid.transform",
                        solid: { name: "sum_solid", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_sq_solid.transform",
                        solid: { name: "sum_sq_solid", __typename: "Solid" },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      }
                    ],
                    __typename: "ExecutionPlan"
                  },
                  __typename: "PipelineRun"
                }
              ],
              environmentType: {
                name: "PandasHelloWorld.Environment",
                __typename: "CompositeType"
              },
              __typename: "Pipeline",
              description: null,
              contexts: [
                {
                  name: "default",
                  description: null,
                  __typename: "PipelineContext",
                  config: {
                    type: {
                      name: "Dict.2",
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          isDict: false,
                          isList: false,
                          isNullable: false,
                          innerTypes: [],
                          description: null,
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        }
                      ],
                      fields: [
                        {
                          name: "log_level",
                          type: { name: "String", __typename: "RegularType" },
                          isOptional: true,
                          __typename: "TypeField"
                        }
                      ],
                      __typename: "CompositeType",
                      description:
                        "A configuration dictionary with typed fields",
                      typeAttributes: {
                        isNamed: true,
                        __typename: "TypeAttributes"
                      }
                    },
                    __typename: "Config"
                  },
                  resources: []
                }
              ],
              solids: [
                {
                  name: "sum_sq_solid",
                  definition: {
                    metadata: [],
                    configDefinition: null,
                    __typename: "SolidDefinition",
                    description: null
                  },
                  inputs: [
                    {
                      definition: {
                        name: "sum_df",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularType",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        },
                        __typename: "InputDefinition",
                        description: null,
                        expectations: []
                      },
                      dependsOn: {
                        definition: {
                          name: "result",
                          __typename: "OutputDefinition"
                        },
                        solid: { name: "sum_solid", __typename: "Solid" },
                        __typename: "Output"
                      },
                      __typename: "Input"
                    }
                  ],
                  outputs: [
                    {
                      definition: {
                        name: "result",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularType",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [],
                      __typename: "Output"
                    }
                  ],
                  __typename: "Solid"
                },
                {
                  name: "load_num_csv",
                  definition: {
                    metadata: [],
                    configDefinition: {
                      type: {
                        description:
                          "A configuration dictionary with typed fields",
                        __typename: "CompositeType",
                        name: "Dict.1",
                        isDict: true,
                        isList: false,
                        isNullable: false,
                        innerTypes: [
                          {
                            name: "Path",
                            __typename: "RegularType",
                            isDict: false,
                            isList: false,
                            isNullable: false,
                            innerTypes: [],
                            description: null,
                            typeAttributes: {
                              isNamed: true,
                              __typename: "TypeAttributes"
                            }
                          }
                        ],
                        fields: [
                          {
                            name: "path",
                            type: { name: "Path", __typename: "RegularType" },
                            isOptional: false,
                            __typename: "TypeField"
                          }
                        ],
                        typeAttributes: {
                          isNamed: true,
                          __typename: "TypeAttributes"
                        }
                      },
                      __typename: "Config"
                    },
                    __typename: "SolidDefinition",
                    description: null
                  },
                  inputs: [],
                  outputs: [
                    {
                      definition: {
                        name: "result",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularType",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [
                        {
                          solid: { name: "sum_solid", __typename: "Solid" },
                          __typename: "Input"
                        }
                      ],
                      __typename: "Output"
                    }
                  ],
                  __typename: "Solid"
                },
                {
                  name: "sum_solid",
                  definition: {
                    metadata: [],
                    configDefinition: null,
                    __typename: "SolidDefinition",
                    description: null
                  },
                  inputs: [
                    {
                      definition: {
                        name: "num",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularType",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        },
                        __typename: "InputDefinition",
                        description: null,
                        expectations: []
                      },
                      dependsOn: {
                        definition: {
                          name: "result",
                          __typename: "OutputDefinition"
                        },
                        solid: { name: "load_num_csv", __typename: "Solid" },
                        __typename: "Output"
                      },
                      __typename: "Input"
                    }
                  ],
                  outputs: [
                    {
                      definition: {
                        name: "result",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularType",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [
                        {
                          solid: { name: "sum_sq_solid", __typename: "Solid" },
                          __typename: "Input"
                        }
                      ],
                      __typename: "Output"
                    }
                  ],
                  __typename: "Solid"
                }
              ]
            }
          ]
        }
      }
    }
  }
];

export default MOCKS;
