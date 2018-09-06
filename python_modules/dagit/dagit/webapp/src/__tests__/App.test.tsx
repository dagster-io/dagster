import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import App, { APP_QUERY } from "../App";
import AppCache from "../AppCache";
import { MockedProvider } from "./MockedProvider";

const mocks = [
  {
    request: {
      operationName: "AppQuery",
      query: APP_QUERY
    },
    result: {
      data: {
        pipelines: [
          {
            __typename: "Pipeline",
            name: "pandas_hello_world",
            description: null,
            solids: [
              {
                __typename: "Solid",
                outputs: [
                  {
                    __typename: "Output",
                    name: "result",
                    type: {
                      __typename: "RegularType",
                      name: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                    },
                    description: null,
                    expectations: []
                  }
                ],
                inputs: [],
                name: "load_num_csv",
                description: null,
                config: {
                  __typename: "Config",
                  type: {
                    __typename: "CompositeType",
                    name: "ConfigDictionary",
                    description:
                      "Configuration dictionary.\n            Typed-checked but then passed to implementations as a python dict",
                    fields: [
                      {
                        __typename: "Field",
                        name: "path",
                        description: null,
                        isOptional: false,
                        defaultValue:
                          "<class 'dagster.core.types.__FieldValueSentinel'>",
                        type: {
                          __typename: "RegularType",
                          name: "Path",
                          description:
                            "\nA string the represents a path. It is very useful for some tooling\nto know that a string indeed represents a file path. That way they\ncan, for example, make the paths relative to a different location\nfor a particular execution environment.\n"
                        }
                      }
                    ]
                  }
                }
              },
              {
                __typename: "Solid",
                outputs: [
                  {
                    __typename: "Output",
                    name: "result",
                    type: {
                      __typename: "RegularType",
                      name: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                    },
                    description: null,
                    expectations: []
                  }
                ],
                inputs: [
                  {
                    __typename: "Input",
                    name: "num",
                    type: {
                      __typename: "RegularType",
                      name: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                    },
                    description: null,
                    expectations: [],
                    dependsOn: {
                      __typename: "Output",
                      name: "result",
                      solid: {
                        __typename: "Solid",
                        name: "load_num_csv"
                      }
                    }
                  }
                ],
                name: "sum_solid",
                description: null,
                config: {
                  __typename: "Config",
                  type: {
                    __typename: "RegularType",
                    name: "Any",
                    description:
                      "The type that allows any value, including no value."
                  }
                }
              },
              {
                __typename: "Solid",
                outputs: [
                  {
                    __typename: "Output",
                    name: "result",
                    type: {
                      __typename: "RegularType",
                      name: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                    },
                    description: null,
                    expectations: []
                  }
                ],
                inputs: [
                  {
                    __typename: "Input",
                    name: "sum_df",
                    type: {
                      __typename: "RegularType",
                      name: "PandasDataFrame",
                      description:
                        "Two-dimensional size-mutable, potentially heterogeneous\ntabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                    },
                    description: null,
                    expectations: [],
                    dependsOn: {
                      __typename: "Output",
                      name: "result",
                      solid: {
                        __typename: "Solid",
                        name: "sum_solid"
                      }
                    }
                  }
                ],
                name: "sum_sq_solid",
                description: null,
                config: {
                  __typename: "Config",
                  type: {
                    __typename: "RegularType",
                    name: "Any",
                    description:
                      "The type that allows any value, including no value."
                  }
                }
              }
            ],
            contexts: [
              {
                __typename: "Context",
                name: "default",
                description: null,
                config: {
                  __typename: "Config",
                  type: {
                    __typename: "CompositeType",
                    name: "ConfigDictionary",
                    description:
                      "Configuration dictionary.\n            Typed-checked but then passed to implementations as a python dict",
                    fields: [
                      {
                        __typename: "Field",
                        name: "log_level",
                        description: null,
                        isOptional: true,
                        defaultValue: "ERROR",
                        type: {
                          __typename: "RegularType",
                          name: "String",
                          description: "A string."
                        }
                      }
                    ]
                  }
                }
              }
            ]
          }
        ]
      }
    }
  }
];

function createNodeMock(element) {
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
