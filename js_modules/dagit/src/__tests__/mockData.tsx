import { APP_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";

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
              description: "A boolean.",
              __typename: "RegularType"
            },
            {
              name: "Bool.MaterializationSchema",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description:
                "Materialization schema for scalar Bool.MaterializationSchema",
              __typename: "CompositeType"
            },
            {
              name: "Dict.1",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.10",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
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
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.3",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.4",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.5",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.6",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.7",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.8",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "Dict.9",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
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
              __typename: "CompositeType"
            },
            {
              name: "PandasDataFrameMaterializationConfigSchema",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.ContextConfig",
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
              name: "PandasHelloWorld.SolidConfig.SumSolid",
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
              name: "PandasHelloWorld.SolidConfig.SumSqSolid",
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
              name: "PandasHelloWorld.SumSolid.Inputs",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SumSolid.Outputs",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: null,
              __typename: "CompositeType"
            },
            {
              name: "PandasHelloWorld.SumSqSolid.Outputs",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
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
              description:
                "\nA string the represents a path. It is very useful for some tooling\nto know that a string indeed represents a file path. That way they\ncan, for example, make the paths relative to a different location\nfor a particular execution environment.\n",
              __typename: "RegularType"
            },
            {
              name: "Path.MaterializationSchema",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description:
                "Materialization schema for scalar Path.MaterializationSchema",
              __typename: "CompositeType"
            },
            {
              name: "String",
              typeAttributes: {
                isBuiltin: true,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description: "A string.",
              __typename: "RegularType"
            },
            {
              name: "String.MaterializationSchema",
              typeAttributes: {
                isBuiltin: false,
                isSystemConfig: false,
                __typename: "TypeAttributes",
                isNamed: true
              },
              description:
                "Materialization schema for scalar String.MaterializationSchema",
              __typename: "CompositeType"
            }
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
          name: "PandasDataFrame",
          description:
            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
          isDict: true,
          isList: false,
          isNullable: false,
          innerTypes: [
            {
              name: "Dict.4",
              __typename: "CompositeType",
              description: null,
              isDict: true,
              isList: false,
              isNullable: false,
              innerTypes: [
                { name: "Path", __typename: "RegularType" },
                { name: "String", __typename: "RegularType" }
              ],
              fields: [
                {
                  name: "path",
                  description: null,
                  type: { name: "Path", __typename: "RegularType" },
                  isOptional: false,
                  __typename: "TypeField"
                },
                {
                  name: "sep",
                  description: null,
                  type: { name: "String", __typename: "RegularType" },
                  isOptional: true,
                  __typename: "TypeField"
                }
              ],
              typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
            },
            {
              name: "Path",
              __typename: "RegularType",
              description:
                "\nA string the represents a path. It is very useful for some tooling\nto know that a string indeed represents a file path. That way they\ncan, for example, make the paths relative to a different location\nfor a particular execution environment.\n",
              isDict: false,
              isList: false,
              isNullable: false,
              innerTypes: [],
              typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
            },
            {
              name: "String",
              __typename: "RegularType",
              description: "A string.",
              isDict: false,
              isList: false,
              isNullable: false,
              innerTypes: [],
              typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
            },
            {
              name: "Dict.5",
              __typename: "CompositeType",
              description: null,
              isDict: true,
              isList: false,
              isNullable: false,
              innerTypes: [{ name: "Path", __typename: "RegularType" }],
              fields: [
                {
                  name: "path",
                  description: null,
                  type: { name: "Path", __typename: "RegularType" },
                  isOptional: false,
                  __typename: "TypeField"
                }
              ],
              typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
            },
            {
              name: "Dict.6",
              __typename: "CompositeType",
              description: null,
              isDict: true,
              isList: false,
              isNullable: false,
              innerTypes: [{ name: "Path", __typename: "RegularType" }],
              fields: [
                {
                  name: "path",
                  description: null,
                  type: { name: "Path", __typename: "RegularType" },
                  isOptional: false,
                  __typename: "TypeField"
                }
              ],
              typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
            }
          ],
          fields: [
            {
              name: "csv",
              description: null,
              type: { name: "Dict.4", __typename: "CompositeType" },
              isOptional: false,
              __typename: "TypeField"
            },
            {
              name: "parquet",
              description: null,
              type: { name: "Dict.5", __typename: "CompositeType" },
              isOptional: false,
              __typename: "TypeField"
            },
            {
              name: "table",
              description: null,
              type: { name: "Dict.6", __typename: "CompositeType" },
              isOptional: false,
              __typename: "TypeField"
            }
          ],
          __typename: "CompositeType",
          typeAttributes: { isNamed: true, __typename: "TypeAttributes" }
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
              runs: [],
              environmentType: {
                name: "PandasHelloWorld.Environment",
                __typename: "CompositeType"
              },
              types: [
                { __typename: "RegularType", name: "Bool" },
                {
                  __typename: "CompositeType",
                  name: "Bool.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.10", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.1",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "sep",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.10",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
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
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.3",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.4",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "sep",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.5",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.6",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.7",
                  fields: [
                    {
                      name: "log_level",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.8",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.9",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrame",
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.4", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.5", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.6", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameMaterializationConfigSchema",
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.1", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.2", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.3", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.ContextConfig",
                  fields: [
                    {
                      name: "default",
                      isOptional: true,
                      type: {
                        name:
                          "PandasHelloWorld.ContextDefinitionConfig.Default",
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
                      isOptional: true,
                      type: { name: "Dict.7", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "resources",
                      isOptional: true,
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
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorld.ContextConfig",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "solids",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorld.SolidsConfigDictionary",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "expectations",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorld.ExpectationsConfig",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "execution",
                      isOptional: true,
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
                      isOptional: true,
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
                      isOptional: true,
                      type: { name: "Bool", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SolidConfig.SumSolid",
                  fields: [
                    {
                      name: "inputs",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorld.SumSolid.Inputs",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "outputs",
                      isOptional: true,
                      type: {
                        name: "List.PandasHelloWorld.SumSolid.Outputs",
                        __typename: "RegularType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SolidConfig.SumSqSolid",
                  fields: [
                    {
                      name: "outputs",
                      isOptional: true,
                      type: {
                        name: "List.PandasHelloWorld.SumSqSolid.Outputs",
                        __typename: "RegularType"
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
                      name: "sum_sq_solid",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorld.SolidConfig.SumSqSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "sum_solid",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorld.SolidConfig.SumSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSolid.Inputs",
                  fields: [
                    {
                      name: "num",
                      isOptional: false,
                      type: {
                        name: "PandasDataFrame",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSolid.Outputs",
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameMaterializationConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSqSolid.Outputs",
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameMaterializationConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "Path" },
                {
                  __typename: "CompositeType",
                  name: "Path.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.8", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "String" },
                {
                  __typename: "CompositeType",
                  name: "String.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.9", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                }
              ],
              __typename: "Pipeline",
              description: null,
              contexts: [
                {
                  name: "default",
                  description: null,
                  __typename: "PipelineContext",
                  config: {
                    type: {
                      name: "Dict.7",
                      description: null,
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          description: "A string.",
                          isDict: false,
                          isList: false,
                          isNullable: false,
                          innerTypes: [],
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        }
                      ],
                      fields: [
                        {
                          name: "log_level",
                          description: null,
                          type: { name: "String", __typename: "RegularType" },
                          isOptional: true,
                          __typename: "TypeField"
                        }
                      ],
                      __typename: "CompositeType",
                      typeAttributes: {
                        isNamed: true,
                        __typename: "TypeAttributes"
                      }
                    },
                    __typename: "TypeField"
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
                          __typename: "CompositeType",
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
                          __typename: "CompositeType",
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
                          __typename: "CompositeType",
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
                      dependsOn: null,
                      __typename: "Input"
                    }
                  ],
                  outputs: [
                    {
                      definition: {
                        name: "result",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "CompositeType",
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
            },
            {
              name: "pandas_hello_world_fails",
              runs: [],
              environmentType: {
                name: "PandasHelloWorldFails.Environment",
                __typename: "CompositeType"
              },
              types: [
                { __typename: "RegularType", name: "Bool" },
                {
                  __typename: "CompositeType",
                  name: "Bool.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.10", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.1",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "sep",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.10",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.11",
                  fields: [
                    {
                      name: "log_level",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.2",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.3",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.4",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "sep",
                      isOptional: true,
                      type: { name: "String", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.5",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.6",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.8",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "Dict.9",
                  fields: [
                    {
                      name: "path",
                      isOptional: false,
                      type: { name: "Path", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrame",
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.4", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.5", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.6", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameMaterializationConfigSchema",
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.1", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.2", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.3", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.AlwaysFailsSolid.Outputs",
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameMaterializationConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ContextConfig",
                  fields: [
                    {
                      name: "default",
                      isOptional: true,
                      type: {
                        name:
                          "PandasHelloWorldFails.ContextDefinitionConfig.Default",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ContextDefinitionConfig.Default",
                  fields: [
                    {
                      name: "config",
                      isOptional: true,
                      type: { name: "Dict.11", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "resources",
                      isOptional: true,
                      type: {
                        name:
                          "PandasHelloWorldFails.ContextDefinitionConfig.Default.Resources",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name:
                    "PandasHelloWorldFails.ContextDefinitionConfig.Default.Resources",
                  fields: []
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.Environment",
                  fields: [
                    {
                      name: "context",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorldFails.ContextConfig",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "solids",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorldFails.SolidsConfigDictionary",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "expectations",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorldFails.ExpectationsConfig",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "execution",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorldFails.ExecutionConfig",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ExecutionConfig",
                  fields: [
                    {
                      name: "serialize_intermediates",
                      isOptional: true,
                      type: { name: "Bool", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ExpectationsConfig",
                  fields: [
                    {
                      name: "evaluate",
                      isOptional: true,
                      type: { name: "Bool", __typename: "RegularType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SolidConfig.AlwaysFailsSolid",
                  fields: [
                    {
                      name: "outputs",
                      isOptional: true,
                      type: {
                        name:
                          "List.PandasHelloWorldFails.AlwaysFailsSolid.Outputs",
                        __typename: "RegularType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SolidConfig.SumSolid",
                  fields: [
                    {
                      name: "inputs",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorldFails.SumSolid.Inputs",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "outputs",
                      isOptional: true,
                      type: {
                        name: "List.PandasHelloWorldFails.SumSolid.Outputs",
                        __typename: "RegularType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SolidConfig.SumSqSolid",
                  fields: [
                    {
                      name: "outputs",
                      isOptional: true,
                      type: {
                        name: "List.PandasHelloWorldFails.SumSqSolid.Outputs",
                        __typename: "RegularType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SolidsConfigDictionary",
                  fields: [
                    {
                      name: "always_fails_solid",
                      isOptional: true,
                      type: {
                        name:
                          "PandasHelloWorldFails.SolidConfig.AlwaysFailsSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "sum_solid",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorldFails.SolidConfig.SumSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "sum_sq_solid",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorldFails.SolidConfig.SumSqSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSolid.Inputs",
                  fields: [
                    {
                      name: "num",
                      isOptional: false,
                      type: {
                        name: "PandasDataFrame",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSolid.Outputs",
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameMaterializationConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSqSolid.Outputs",
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameMaterializationConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "Path" },
                {
                  __typename: "CompositeType",
                  name: "Path.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.8", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "String" },
                {
                  __typename: "CompositeType",
                  name: "String.MaterializationSchema",
                  fields: [
                    {
                      name: "json",
                      isOptional: false,
                      type: { name: "Dict.9", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                }
              ],
              __typename: "Pipeline",
              description: null,
              contexts: [
                {
                  name: "default",
                  description: null,
                  __typename: "PipelineContext",
                  config: {
                    type: {
                      name: "Dict.11",
                      description: null,
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          description: "A string.",
                          isDict: false,
                          isList: false,
                          isNullable: false,
                          innerTypes: [],
                          typeAttributes: {
                            isNamed: true,
                            __typename: "TypeAttributes"
                          }
                        }
                      ],
                      fields: [
                        {
                          name: "log_level",
                          description: null,
                          type: { name: "String", __typename: "RegularType" },
                          isOptional: true,
                          __typename: "TypeField"
                        }
                      ],
                      __typename: "CompositeType",
                      typeAttributes: {
                        isNamed: true,
                        __typename: "TypeAttributes"
                      }
                    },
                    __typename: "TypeField"
                  },
                  resources: []
                }
              ],
              solids: [
                {
                  name: "always_fails_solid",
                  definition: {
                    metadata: [],
                    configDefinition: null,
                    __typename: "SolidDefinition",
                    description: null
                  },
                  inputs: [
                    {
                      definition: {
                        name: "sum_sq_solid",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "CompositeType",
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
                        solid: { name: "sum_sq_solid", __typename: "Solid" },
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
                          __typename: "CompositeType",
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
                          __typename: "CompositeType",
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
                      dependsOn: null,
                      __typename: "Input"
                    }
                  ],
                  outputs: [
                    {
                      definition: {
                        name: "result",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "CompositeType",
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
                          __typename: "CompositeType",
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
                          __typename: "CompositeType",
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
                          solid: {
                            name: "always_fails_solid",
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
  }
];

export default MOCKS;
