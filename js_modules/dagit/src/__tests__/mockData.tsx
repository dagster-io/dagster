import { APP_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";

const MOCKS = [
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
                { __typename: "RegularType", name: "Bool", isSelector: false },
                {
                  __typename: "CompositeType",
                  name: "Dict.3",
                  isSelector: false,
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
                  name: "Dict.4",
                  isSelector: false,
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
                  name: "Dict.5",
                  isSelector: false,
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
                  isSelector: false,
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
                  name: "Dict.7",
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
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
                  __typename: "RegularType",
                  name: "PandasDataFrame",
                  isSelector: false
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameInputSchema",
                  isSelector: true,
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.3", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.4", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.5", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameOutputConfigSchema",
                  isSelector: true,
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.6", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.7", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.8", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.ContextConfig",
                  isSelector: true,
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
                  isSelector: false,
                  fields: [
                    {
                      name: "config",
                      isOptional: true,
                      type: { name: "Dict.9", __typename: "CompositeType" },
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
                  isSelector: false,
                  fields: []
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.Environment",
                  isSelector: false,
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
                  isSelector: false,
                  fields: []
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.ExpectationsConfig",
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
                  fields: [
                    {
                      name: "sum_solid",
                      isOptional: false,
                      type: {
                        name: "PandasHelloWorld.SolidConfig.SumSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "sum_sq_solid",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorld.SolidConfig.SumSqSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSolid.Inputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "num",
                      isOptional: false,
                      type: {
                        name: "PandasDataFrameInputSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSolid.Outputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameOutputConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorld.SumSqSolid.Outputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameOutputConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "Path", isSelector: false },
                { __typename: "RegularType", name: "String", isSelector: false }
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
                      name: "Dict.9",
                      description:
                        "A configuration dictionary with typed fields",
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          description: "",
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
                { __typename: "RegularType", name: "Bool", isSelector: false },
                {
                  __typename: "CompositeType",
                  name: "Dict.10",
                  isSelector: false,
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
                  name: "Dict.3",
                  isSelector: false,
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
                  name: "Dict.4",
                  isSelector: false,
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
                  name: "Dict.5",
                  isSelector: false,
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
                  isSelector: false,
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
                  name: "Dict.7",
                  isSelector: false,
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
                  isSelector: false,
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
                  __typename: "RegularType",
                  name: "PandasDataFrame",
                  isSelector: false
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameInputSchema",
                  isSelector: true,
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.3", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.4", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.5", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasDataFrameOutputConfigSchema",
                  isSelector: true,
                  fields: [
                    {
                      name: "csv",
                      isOptional: false,
                      type: { name: "Dict.6", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "parquet",
                      isOptional: false,
                      type: { name: "Dict.7", __typename: "CompositeType" },
                      __typename: "TypeField"
                    },
                    {
                      name: "table",
                      isOptional: false,
                      type: { name: "Dict.8", __typename: "CompositeType" },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.AlwaysFailsSolid.Outputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameOutputConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ContextConfig",
                  isSelector: true,
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
                  isSelector: false,
                  fields: [
                    {
                      name: "config",
                      isOptional: true,
                      type: { name: "Dict.10", __typename: "CompositeType" },
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
                  isSelector: false,
                  fields: []
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.Environment",
                  isSelector: false,
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
                  isSelector: false,
                  fields: []
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.ExpectationsConfig",
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
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
                  isSelector: false,
                  fields: [
                    {
                      name: "sum_sq_solid",
                      isOptional: true,
                      type: {
                        name: "PandasHelloWorldFails.SolidConfig.SumSqSolid",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    },
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
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSolid.Inputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "num",
                      isOptional: false,
                      type: {
                        name: "PandasDataFrameInputSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSolid.Outputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameOutputConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                {
                  __typename: "CompositeType",
                  name: "PandasHelloWorldFails.SumSqSolid.Outputs",
                  isSelector: false,
                  fields: [
                    {
                      name: "result",
                      isOptional: true,
                      type: {
                        name: "PandasDataFrameOutputConfigSchema",
                        __typename: "CompositeType"
                      },
                      __typename: "TypeField"
                    }
                  ]
                },
                { __typename: "RegularType", name: "Path", isSelector: false },
                { __typename: "RegularType", name: "String", isSelector: false }
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
                      name: "Dict.10",
                      description:
                        "A configuration dictionary with typed fields",
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          description: "",
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
                },
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
          isDict: false,
          isList: false,
          isNullable: false,
          innerTypes: [],
          typeAttributes: { isNamed: true, __typename: "TypeAttributes" },
          __typename: "RegularType"
        }
      }
    }
  },

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
              description: "",
              __typename: "RegularType"
            },
            {
              name: "Dict.3",
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
              name: "Dict.4",
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
              name: "Dict.5",
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
              name: "Dict.6",
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
              name: "Dict.7",
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
              name: "Dict.8",
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
              name: "Dict.9",
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
              name: "PandasDataFrameInputSchema",
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
              name: "PandasDataFrameOutputConfigSchema",
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
                isBuiltin: false,
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
                isBuiltin: false,
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
                isBuiltin: false,
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
              description: "",
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
              description: "",
              __typename: "RegularType"
            }
          ]
        }
      }
    }
  }
];

export default MOCKS;
