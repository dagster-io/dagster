import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import App, { APP_QUERY } from "../App";
import AppCache from "../AppCache";
import { MockedProvider } from "./MockedProvider";
const mocks = [
  {
    request: {
      operationName: "PipelineseContainerQuery",
      query: APP_QUERY
    },
    result: {
      data: {
        pipelinesOrErrors: [
          {
            name: "pandas_hello_world",
            description: null,
            solids: [
              {
                outputs: [
                  {
                    definition: {
                      name: "result",
                      type: {
                        name: "PandasDataFrame",
                        description:
                          "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                        __typename: "RegularType"
                      },
                      __typename: "OutputDefinition",
                      description: null,
                      expectations: []
                    },
                    __typename: "Output"
                  }
                ],
                inputs: [
                  {
                    definition: {
                      name: "num",
                      type: {
                        name: "PandasDataFrame",
                        description:
                          "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                        __typename: "RegularType"
                      },
                      __typename: "InputDefinition",
                      description: null,
                      expectations: []
                    },
                    __typename: "Input",
                    dependsOn: {
                      definition: {
                        name: "result",
                        __typename: "OutputDefinition"
                      },
                      solid: { name: "load_num_csv", __typename: "Solid" },
                      __typename: "Output"
                    }
                  }
                ],
                __typename: "Solid",
                name: "sum_solid",
                definition: {
                  description: null,
                  configDefinition: null,
                  __typename: "SolidDefinition",
                  name: "sum_solid"
                }
              },
              {
                outputs: [
                  {
                    definition: {
                      name: "result",
                      type: {
                        name: "PandasDataFrame",
                        description:
                          "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                        __typename: "RegularType"
                      },
                      __typename: "OutputDefinition",
                      description: null,
                      expectations: []
                    },
                    __typename: "Output"
                  }
                ],
                inputs: [
                  {
                    definition: {
                      name: "sum_df",
                      type: {
                        name: "PandasDataFrame",
                        description:
                          "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                        __typename: "RegularType"
                      },
                      __typename: "InputDefinition",
                      description: null,
                      expectations: []
                    },
                    __typename: "Input",
                    dependsOn: {
                      definition: {
                        name: "result",
                        __typename: "OutputDefinition"
                      },
                      solid: { name: "sum_solid", __typename: "Solid" },
                      __typename: "Output"
                    }
                  }
                ],
                __typename: "Solid",
                name: "sum_sq_solid",
                definition: {
                  description: null,
                  configDefinition: null,
                  __typename: "SolidDefinition",
                  name: "sum_sq_solid"
                }
              },
              {
                outputs: [
                  {
                    definition: {
                      name: "result",
                      type: {
                        name: "PandasDataFrame",
                        description:
                          "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/",
                        __typename: "RegularType"
                      },
                      __typename: "OutputDefinition",
                      description: null,
                      expectations: []
                    },
                    __typename: "Output"
                  }
                ],
                inputs: [],
                __typename: "Solid",
                name: "load_num_csv",
                definition: {
                  description: null,
                  configDefinition: {
                    type: {
                      __typename: "CompositeType",
                      name: "LoadDataFrameConfigDict",
                      description:
                        "Configuration dictionary.\n\n    Typed-checked but then passed to implementations as a python dict\n\n    Arguments:\n      fields (dict): dictonary of :py:class:`Field` objects keyed by name",
                      fields: [
                        {
                          name: "path",
                          description: null,
                          isOptional: false,
                          defaultValue:
                            "<class 'dagster.core.types.__FieldValueSentinel'>",
                          type: {
                            name: "Path",
                            description:
                              "\nA string the represents a path. It is very useful for some tooling\nto know that a string indeed represents a file path. That way they\ncan, for example, make the paths relative to a different location\nfor a particular execution environment.\n",
                            __typename: "RegularType"
                          },
                          __typename: "TypeField"
                        }
                      ]
                    },
                    __typename: "Config"
                  },
                  __typename: "SolidDefinition",
                  name: "load_num_csv"
                }
              }
            ],
            contexts: [
              {
                name: "default",
                description: null,
                config: {
                  type: {
                    __typename: "CompositeType",
                    name: "DefaultContextConfigDict",
                    description:
                      "Configuration dictionary.\n\n    Typed-checked but then passed to implementations as a python dict\n\n    Arguments:\n      fields (dict): dictonary of :py:class:`Field` objects keyed by name",
                    fields: [
                      {
                        name: "log_level",
                        description: null,
                        isOptional: true,
                        defaultValue: "INFO",
                        type: {
                          name: "String",
                          description: "A string.",
                          __typename: "RegularType"
                        },
                        __typename: "TypeField"
                      }
                    ]
                  },
                  __typename: "Config"
                },
                __typename: "PipelineContext"
              }
            ],
            __typename: "Pipeline"
          }
        ]
      }
    }
  }
];

function createNodeMock(element: any) {
  if (element.type === "div") {
    return {
      querySelector() {
        return null;
      },
      querySelectorAll() {
        return [];
      }
    };
  }
  return null;
}

it("renders without error", async () => {
  const component = TestRenderer.create(
    <MockedProvider mocks={mocks} addTypename={true} cache={AppCache}>
      <App />
    </MockedProvider>,
    { createNodeMock }
  );

  await new Promise(resolve => setTimeout(resolve, 1000));

  const tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});
