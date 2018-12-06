import { APP_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { CONFIG_CODE_EDITOR_CONTAINER_QUERY } from "../configeditor/ConfigCodeEditorContainer";

const MOCKS = [
  {
    request: {
      operationName: "PipelineseContainerQuery",
      query: APP_QUERY
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
                  runId: "a066d459-ed9e-4286-9a5a-2c7cf3b5876c",
                  status: "SUCCESS",
                  logs: {
                    nodes: [
                      {
                        __typename: "PipelineStartEvent",
                        message:
                          "Beginning execution of pipeline pandas_hello_world",
                        timestamp: "1544082799816"
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          "About to execute the compute node graph in the following order ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544082799817"
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          "Entering execute_steps loop. Order: ['load_num_csv.transform', 'sum_solid.transform', 'sum_sq_solid.transform']",
                        timestamp: "1544082799817"
                      },
                      {
                        __typename: "ExecutionStepStartEvent",
                        message:
                          "Beginning execution of load_num_csv.transform",
                        timestamp: "1544082799817",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          "Executing core transform for solid load_num_csv.",
                        timestamp: "1544082799817"
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          'Solid load_num_csv emitted output "result" value    num1  num2\n0     1     2\n1     3     4',
                        timestamp: "1544082799828"
                      },
                      {
                        __typename: "ExecutionStepSuccessEvent",
                        message:
                          "Execution of load_num_csv.transform succeeded in 11.127233505249023",
                        timestamp: "1544082799828",
                        step: {
                          name: "load_num_csv.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "ExecutionStepStartEvent",
                        message: "Beginning execution of sum_solid.transform",
                        timestamp: "1544082799829",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          "Executing core transform for solid sum_solid.",
                        timestamp: "1544082799829"
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          'Solid sum_solid emitted output "result" value    num1  num2  sum\n0     1     2    3\n1     3     4    7',
                        timestamp: "1544082799837"
                      },
                      {
                        __typename: "ExecutionStepSuccessEvent",
                        message:
                          "Execution of sum_solid.transform succeeded in 8.054018020629883",
                        timestamp: "1544082799837",
                        step: {
                          name: "sum_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "ExecutionStepStartEvent",
                        message:
                          "Beginning execution of sum_sq_solid.transform",
                        timestamp: "1544082799837",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          "Executing core transform for solid sum_sq_solid.",
                        timestamp: "1544082799838"
                      },
                      {
                        __typename: "LogMessageEvent",
                        message:
                          'Solid sum_sq_solid emitted output "result" value    num1  num2  sum  sum_sq\n0     1     2    3       9\n1     3     4    7      49',
                        timestamp: "1544082799845"
                      },
                      {
                        __typename: "ExecutionStepSuccessEvent",
                        message:
                          "Execution of sum_sq_solid.transform succeeded in 7.702827453613281",
                        timestamp: "1544082799845",
                        step: {
                          name: "sum_sq_solid.transform",
                          __typename: "ExecutionStep"
                        }
                      },
                      {
                        __typename: "PipelineSuccessEvent",
                        message:
                          "Completing successful execution of pipeline pandas_hello_world",
                        timestamp: "1544082799846"
                      }
                    ],
                    __typename: "LogMessageConnection",
                    pageInfo: {
                      lastCursor: "15",
                      __typename: "PageInfo"
                    }
                  },
                  executionPlan: {
                    steps: [
                      {
                        name: "load_num_csv.transform",
                        solid: {
                          name: "load_num_csv",
                          __typename: "Solid"
                        },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_solid.transform",
                        solid: {
                          name: "sum_solid",
                          __typename: "Solid"
                        },
                        tag: "TRANSFORM",
                        __typename: "ExecutionStep"
                      },
                      {
                        name: "sum_sq_solid.transform",
                        solid: {
                          name: "sum_sq_solid",
                          __typename: "Solid"
                        },
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
                      __typename: "CompositeType",
                      name: "DefaultContextConfigDict",
                      description:
                        "A configuration dictionary with typed fields",
                      fields: [
                        {
                          name: "log_level",
                          description: null,
                          isOptional: true,
                          defaultValue: "INFO",
                          type: {
                            name: "String",
                            description: null,
                            __typename: "RegularType"
                          },
                          __typename: "TypeField"
                        }
                      ]
                    },
                    __typename: "Config"
                  }
                }
              ],
              solids: [
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
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
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
                        solid: {
                          name: "load_num_csv",
                          __typename: "Solid"
                        },
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
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [
                        {
                          solid: {
                            name: "sum_sq_solid",
                            __typename: "Solid"
                          },
                          __typename: "Input"
                        }
                      ],
                      __typename: "Output"
                    }
                  ],
                  __typename: "Solid"
                },
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
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
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
                        solid: {
                          name: "sum_solid",
                          __typename: "Solid"
                        },
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
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
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
                        name: "LoadDataFrameConfigDict",
                        fields: [
                          {
                            name: "path",
                            description: null,
                            isOptional: false,
                            defaultValue: null,
                            type: {
                              name: "Path",
                              description: null,
                              __typename: "RegularType"
                            },
                            __typename: "TypeField"
                          }
                        ]
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
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [
                        {
                          solid: {
                            name: "sum_solid",
                            __typename: "Solid"
                          },
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
  },
  {
    request: {
      operationName: "TypeExplorerContainerQuery",
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
            __typename: "TypeAttributes"
          }
        }
      }
    }
  },
  {
    request: {
      operationName: "ConfigCodeEditorContainerQuery",
      query: CONFIG_CODE_EDITOR_CONTAINER_QUERY,
      variables: {
        pipelineName: "pandas_hello_world"
      }
    },
    result: {
      data: {
        pipelineOrError: {
          __typename: "Pipeline",
          types: [
            {
              __typename: "RegularType",
              name: "Bool"
            },
            {
              __typename: "CompositeType",
              name: "DefaultContextConfigDict",
              fields: [
                {
                  name: "log_level",
                  type: {
                    name: "String",
                    __typename: "RegularType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "CompositeType",
              name: "LoadDataFrameConfigDict",
              fields: [
                {
                  name: "path",
                  type: {
                    name: "Path",
                    __typename: "RegularType"
                  },
                  __typename: "TypeField"
                }
              ]
            },
            {
              __typename: "RegularType",
              name: "PandasDataFrame"
            },
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
                  type: {
                    name: "DefaultContextConfigDict",
                    __typename: "CompositeType"
                  },
                  __typename: "TypeField"
                }
              ]
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
                  type: {
                    name: "Bool",
                    __typename: "RegularType"
                  },
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
                  type: {
                    name: "Bool",
                    __typename: "RegularType"
                  },
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
                  type: {
                    name: "LoadDataFrameConfigDict",
                    __typename: "CompositeType"
                  },
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
            {
              __typename: "RegularType",
              name: "Path"
            },
            {
              __typename: "RegularType",
              name: "String"
            }
          ]
        }
      }
    }
  },
  {
    request: {
      operationName: "TypeListContainerQuery",
      query: TYPE_LIST_CONTAINER_QUERY,
      variables: {
        pipelineName: "pandas_hello_world"
      }
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
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "RegularType"
            },
            {
              name: "DefaultContextConfigDict",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes"
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "LoadDataFrameConfigDict",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes"
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "PandasDataFrame",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes"
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
                __typename: "TypeAttributes"
              },
              description: "A configuration dictionary with typed fields",
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ContextDefinitionConfig.Default",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.Environment",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ExecutionConfig",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ExpectationsConfig",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SolidConfig.LoadNumCsv",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SolidsConfigDictionary",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: true,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Path",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "RegularType"
            },
            {
              name: "String",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes"
              },
              description: null,
              __typename: "RegularType"
            }
          ]
        }
      }
    }
  }
];

export default MOCKS;
