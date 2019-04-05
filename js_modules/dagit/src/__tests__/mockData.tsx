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
          runtimeTypes: [
            {
              name: "Any",
              isBuiltin: true,
              displayName: "Any",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Bool",
              isBuiltin: true,
              displayName: "Bool",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Float",
              isBuiltin: true,
              displayName: "Float",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "Int",
              isBuiltin: true,
              displayName: "Int",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "PandasDataFrame",
              isBuiltin: false,
              displayName: "PandasDataFrame",
              description:
                "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/",
              __typename: "RegularRuntimeType"
            },
            {
              name: "Path",
              isBuiltin: true,
              displayName: "Path",
              description: null,
              __typename: "RegularRuntimeType"
            },
            {
              name: "String",
              isBuiltin: true,
              displayName: "String",
              description: null,
              __typename: "RegularRuntimeType"
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
        runtimeTypeName: "PandasDataFrame"
      }
    },
    result: {
      data: {
        runtimeTypeOrError: {
          __typename: "RegularRuntimeType",
          name: "PandasDataFrame",
          description:
            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/",
          inputSchemaType: {
            key: "DataFrameInputSchema",
            name: "DataFrameInputSchema",
            description: null,
            isList: false,
            isNullable: false,
            isSelector: true,
            innerTypes: [
              {
                key: "Dict.28",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.26",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [
                  { key: "String", __typename: "RegularConfigType" },
                  { key: "Path", __typename: "RegularConfigType" }
                ],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  },
                  {
                    name: "sep",
                    description: null,
                    isOptional: true,
                    configType: {
                      key: "String",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Path",
                __typename: "RegularConfigType",
                name: "Path",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "String",
                __typename: "RegularConfigType",
                name: "String",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "Dict.27",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              }
            ],
            fields: [
              {
                name: "csv",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.26",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "parquet",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.27",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "table",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.28",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              }
            ],
            __typename: "CompositeConfigType"
          },
          outputSchemaType: {
            key: "DataFrameOutputSchema",
            name: "DataFrameOutputSchema",
            description: null,
            isList: false,
            isNullable: false,
            isSelector: true,
            innerTypes: [
              {
                key: "Path",
                __typename: "RegularConfigType",
                name: "Path",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "Dict.25",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "String",
                __typename: "RegularConfigType",
                name: "String",
                description: "",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: []
              },
              {
                key: "Dict.24",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [{ key: "Path", __typename: "RegularConfigType" }],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              },
              {
                key: "Dict.23",
                __typename: "CompositeConfigType",
                name: null,
                description: "A configuration dictionary with typed fields",
                isList: false,
                isNullable: false,
                isSelector: false,
                innerTypes: [
                  { key: "String", __typename: "RegularConfigType" },
                  { key: "Path", __typename: "RegularConfigType" }
                ],
                fields: [
                  {
                    name: "path",
                    description: null,
                    isOptional: false,
                    configType: {
                      key: "Path",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  },
                  {
                    name: "sep",
                    description: null,
                    isOptional: true,
                    configType: {
                      key: "String",
                      __typename: "RegularConfigType"
                    },
                    __typename: "ConfigTypeField"
                  }
                ]
              }
            ],
            fields: [
              {
                name: "csv",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.23",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "parquet",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.24",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              },
              {
                name: "table",
                description: null,
                isOptional: false,
                configType: {
                  key: "Dict.25",
                  __typename: "CompositeConfigType"
                },
                __typename: "ConfigTypeField"
              }
            ],
            __typename: "CompositeConfigType"
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
              description: null,
              contexts: [
                {
                  name: "default",
                  description: null,
                  __typename: "PipelineContext",
                  config: {
                    configType: {
                      key: "Dict.32",
                      name: null,
                      description:
                        "A configuration dictionary with typed fields",
                      isList: false,
                      isNullable: false,
                      isSelector: false,
                      innerTypes: [
                        {
                          key: "log_level",
                          __typename: "EnumConfigType",
                          name: "log_level",
                          description: null,
                          isList: false,
                          isNullable: false,
                          isSelector: false,
                          innerTypes: []
                        }
                      ],
                      fields: [
                        {
                          name: "log_level",
                          description: null,
                          isOptional: true,
                          configType: {
                            key: "log_level",
                            __typename: "EnumConfigType"
                          },
                          __typename: "ConfigTypeField"
                        }
                      ],
                      __typename: "CompositeConfigType"
                    },
                    __typename: "ConfigTypeField"
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
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                        },
                        __typename: "InputDefinition",
                        description: null,
                        expectations: []
                      },
                      dependsOn: {
                        definition: {
                          name: "result",
                          type: {
                            name: "PandasDataFrame",
                            __typename: "RegularRuntimeType"
                          },
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
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
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
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
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
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
                        },
                        expectations: [],
                        __typename: "OutputDefinition",
                        description: null
                      },
                      dependedBy: [
                        {
                          solid: { name: "sum_sq_solid", __typename: "Solid" },
                          definition: {
                            name: "sum_df",
                            type: {
                              name: "PandasDataFrame",
                              __typename: "RegularRuntimeType"
                            },
                            __typename: "InputDefinition"
                          },
                          __typename: "Input"
                        }
                      ],
                      __typename: "Output"
                    }
                  ],
                  __typename: "Solid"
                }
              ],
              __typename: "Pipeline",
              environmentType: {
                name: "PandasHelloWorld.Environment",
                __typename: "CompositeConfigType"
              }
            },
            {
              name: "papermill_pandas_hello_world_pipeline",
              description: null,
              contexts: [
                {
                  name: "default",
                  description: null,
                  __typename: "PipelineContext",
                  config: {
                    configType: {
                      key: "Dict.29",
                      name: null,
                      description:
                        "A configuration dictionary with typed fields",
                      isList: false,
                      isNullable: false,
                      isSelector: false,
                      innerTypes: [
                        {
                          key: "log_level",
                          __typename: "EnumConfigType",
                          name: "log_level",
                          description: null,
                          isList: false,
                          isNullable: false,
                          isSelector: false,
                          innerTypes: []
                        }
                      ],
                      fields: [
                        {
                          name: "log_level",
                          description: null,
                          isOptional: true,
                          configType: {
                            key: "log_level",
                            __typename: "EnumConfigType"
                          },
                          __typename: "ConfigTypeField"
                        }
                      ],
                      __typename: "CompositeConfigType"
                    },
                    __typename: "ConfigTypeField"
                  },
                  resources: []
                }
              ],
              solids: [
                {
                  name: "papermill_pandas_hello_world",
                  definition: {
                    metadata: [
                      {
                        key: "notebook_path",
                        value:
                          "/Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster-pandas/dagster_pandas/examples/notebooks/papermill_pandas_hello_world.ipynb",
                        __typename: "SolidMetadataItemDefinition"
                      },
                      {
                        key: "kind",
                        value: "ipynb",
                        __typename: "SolidMetadataItemDefinition"
                      }
                    ],
                    configDefinition: null,
                    __typename: "SolidDefinition",
                    description:
                      "This solid is backed by the notebook at /Users/bengotow/Work/F376/Projects/dagster/python_modules/dagster-pandas/dagster_pandas/examples/notebooks/papermill_pandas_hello_world.ipynb"
                  },
                  inputs: [
                    {
                      definition: {
                        name: "df",
                        type: {
                          name: "PandasDataFrame",
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
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
                          __typename: "RegularRuntimeType",
                          displayName: "PandasDataFrame",
                          description:
                            "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns).\n    See http://pandas.pydata.org/"
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
              ],
              __typename: "Pipeline",
              environmentType: {
                name: "PapermillPandasHelloWorldPipeline.Environment",
                __typename: "CompositeConfigType"
              }
            }
          ]
        }
      }
    }
  }
];

export default MOCKS;
