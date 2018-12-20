import { APP_QUERY } from "../App";
import { TYPE_EXPLORER_CONTAINER_QUERY } from "../typeexplorer/TypeExplorerContainer";
import { TYPE_LIST_CONTAINER_QUERY } from "../typeexplorer/TypeListContainer";
import { CONFIG_CODE_EDITOR_CONTAINER_QUERY } from "../configeditor/ConfigCodeEditorContainer";

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
                      description:
                        "A configuration dictionary with typed fields",
                      isDict: true,
                      isList: false,
                      isNullable: false,
                      innerTypes: [
                        {
                          name: "String",
                          __typename: "RegularType",
                          description: null,
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
                            description: null,
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
                            name: "path",
                            description: null,
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
  }
];

export default MOCKS;
