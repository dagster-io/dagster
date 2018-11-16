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
            __typename: "Pipeline",
            name: "pandas_hello_world",
            description: null,
            contexts: [
              {
                name: "default",
                description: null,
                config: {
                  type: {
                    __typename: "CompositeType",
                    name: "DefaultContextConfigDict",
                    description: "A configuration dictionary with typed fields",
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
                },
                __typename: "PipelineContext"
              }
            ],
            solids: [
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
                          "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                      },
                      expectations: [],
                      __typename: "OutputDefinition",
                      description: null
                    },
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
                          "Two-dimensional size-mutable, potentially heterogeneous\n    tabular data structure with labeled axes (rows and columns). See http://pandas.pydata.org/"
                      },
                      expectations: [],
                      __typename: "OutputDefinition",
                      description: null
                    },
                    __typename: "Output"
                  }
                ],
                __typename: "Solid"
              }
            ],
            environmentType: {
              name: "PandasHelloWorld.Environment",
              __typename: "CompositeType"
            }
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
      },
      getBoundingClientRect() {
        return {
          left: 0,
          top: 0,
          right: 1000,
          bottom: 1000,
          x: 0,
          y: 0,
          width: 1000,
          height: 1000
        };
      }
    };
  }
  return null;
}

async function testApp() {
  const component = TestRenderer.create(
    <MockedProvider mocks={mocks} addTypename={true} cache={AppCache}>
      <App />
    </MockedProvider>,
    { createNodeMock }
  );

  await new Promise(resolve => setTimeout(resolve, 1000));

  const tree = component.toJSON();
  expect(tree).toMatchSnapshot();
}

it("renders without error", async () => {
  await testApp();
});

it("renders pipeline page", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world");
  });
  await testApp();
});

it("renders pipeline solid page", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world/load_num_csv");
  });
  await testApp();
});

it("renders type page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/pandas_hello_world/load_num_csv?type=String"
    );
  });
  await testApp();
});

it("renders editor", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world?editor=true");
  });
  await testApp();
});
