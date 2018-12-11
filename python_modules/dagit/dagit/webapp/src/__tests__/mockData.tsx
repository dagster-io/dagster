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
                      name: "Dict_2",
                      description:
                        "A configuration dictionary with typed fields",
                      typeAttributes: {
                        isNamed: true,
                        __typename: "TypeAttributes"
                      },
                      __typename: "CompositeType"
                    },
                    __typename: "Config"
                  }
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
                        name: "Dict_1",
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
              ],
              types: [
                {
                  __typename: "RegularType",
                  name: "Bool",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "path",
                      description: null,
                      isOptional: false,
                      defaultValue: null,
                      type: { __typename: "RegularType", name: "Path" },
                      __typename: "TypeField"
                    }
                  ],
                  name: "Dict_1",
                  description: "A configuration dictionary with typed fields",
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "log_level",
                      description: null,
                      isOptional: true,
                      defaultValue: "INFO",
                      type: { __typename: "RegularType", name: "String" },
                      __typename: "TypeField"
                    }
                  ],
                  name: "Dict_2",
                  description: "A configuration dictionary with typed fields",
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "RegularType",
                  name: "PandasDataFrame",
                  description:
                    "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "default",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function Field.__init__.<locals>.<lambda> at 0x11d43f510>",
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.ContextDefinitionConfig.Default"
                      },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.ContextConfig",
                  description: "A configuration dictionary with typed fields",
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "config",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function Field.__init__.<locals>.<lambda> at 0x11d43fae8>",
                      type: { __typename: "CompositeType", name: "Dict_2" },
                      __typename: "TypeField"
                    },
                    {
                      name: "resources",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function Field.__init__.<locals>.<lambda> at 0x11d43fa60>",
                      type: {
                        __typename: "CompositeType",
                        name:
                          "PandasHelloWorld.ContextDefinitionConfig.Default.Resources"
                      },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.ContextDefinitionConfig.Default",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [],
                  name:
                    "PandasHelloWorld.ContextDefinitionConfig.Default.Resources",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "context",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function define_maybe_optional_selector_field.<locals>.<lambda> at 0x11c2e8158>",
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.ContextConfig"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "solids",
                      description: null,
                      isOptional: false,
                      defaultValue: null,
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.SolidsConfigDictionary"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "expectations",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function Field.__init__.<locals>.<lambda> at 0x11c2e81e0>",
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.ExpectationsConfig"
                      },
                      __typename: "TypeField"
                    },
                    {
                      name: "execution",
                      description: null,
                      isOptional: true,
                      defaultValue:
                        "<function Field.__init__.<locals>.<lambda> at 0x11c2e8268>",
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.ExecutionConfig"
                      },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.Environment",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "serialize_intermediates",
                      description: null,
                      isOptional: true,
                      defaultValue: "False",
                      type: { __typename: "RegularType", name: "Bool" },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.ExecutionConfig",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "evaluate",
                      description: null,
                      isOptional: true,
                      defaultValue: "True",
                      type: { __typename: "RegularType", name: "Bool" },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.ExpectationsConfig",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "config",
                      description: null,
                      isOptional: false,
                      defaultValue: null,
                      type: { __typename: "CompositeType", name: "Dict_1" },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.SolidConfig.LoadNumCsv",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "CompositeType",
                  fields: [
                    {
                      name: "load_num_csv",
                      description: null,
                      isOptional: false,
                      defaultValue: null,
                      type: {
                        __typename: "CompositeType",
                        name: "PandasHelloWorld.SolidConfig.LoadNumCsv"
                      },
                      __typename: "TypeField"
                    }
                  ],
                  name: "PandasHelloWorld.SolidsConfigDictionary",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "RegularType",
                  name: "Path",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
                },
                {
                  __typename: "RegularType",
                  name: "String",
                  description: null,
                  typeAttributes: {
                    isNamed: true,
                    __typename: "TypeAttributes"
                  }
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
              name: "Dict_1",
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
              name: "Dict_2",
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
                  type: { name: "Dict_2", __typename: "CompositeType" },
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
                  type: { name: "Dict_1", __typename: "CompositeType" },
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
              name: "Dict_1",
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
              name: "Dict_2",
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
