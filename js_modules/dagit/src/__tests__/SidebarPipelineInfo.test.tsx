import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import SidebarPipelineInfo from "../SidebarPipelineInfo";
import { SidebarPipelineInfoFragment } from "../types/SidebarPipelineInfoFragment";

it("renders given a pipeline with resources and loggers", () => {
  const sidebarPipelineInfoData: SidebarPipelineInfoFragment = {
    __typename: "Pipeline",
    name: "A good test pipeline",
    description: "Very friendly and helpful",
    modes: [
      {
        __typename: "Mode",
        name: "one_good_mode",
        description: "A way to run your pipeline",
        resources: [
          {
            __typename: "Resource",
            name: "a_resource",
            description: "Very useful",
            configField: {
              __typename: "ConfigTypeField",
              configType: {
                __typename: "NullableConfigType",
                name: "config",
                key: "Dict.88",
                description: "A configuration dictionary with typed fields",
                innerTypes: [
                  {
                    __typename: "RegularConfigType",
                    name: "foo",
                    key: "Int",
                    description: null,
                    innerTypes: [],
                    isNullable: false,
                    isList: false,
                    isSelector: false
                  }
                ],
                isList: false,
                isNullable: true,
                isSelector: false
              }
            }
          }
        ],
        loggers: []
      },
      {
        __typename: "Mode",
        name: "another_mode",
        description: "Another nice way to run your pipeline",
        resources: [
          {
            __typename: "Resource",
            name: "a_resource",
            description: "Very useful",
            configField: {
              __typename: "ConfigTypeField",
              configType: {
                __typename: "NullableConfigType",
                name: "config",
                key: "Dict.88",
                description: "A configuration dictionary with typed fields",
                innerTypes: [
                  {
                    __typename: "RegularConfigType",
                    name: "foo",
                    key: "Int",
                    description: null,
                    innerTypes: [],
                    isNullable: false,
                    isList: false,
                    isSelector: false
                  }
                ],
                isList: false,
                isNullable: true,
                isSelector: false
              }
            }
          },
          {
            __typename: "Resource",
            name: "b_resource",
            description: "Very useful",
            configField: {
              __typename: "ConfigTypeField",
              configType: {
                __typename: "NullableConfigType",
                name: "config",
                key: "Dict.88",
                description: "A configuration dictionary with typed fields",
                innerTypes: [
                  {
                    __typename: "RegularConfigType",
                    name: "foo",
                    key: "Int",
                    description: null,
                    innerTypes: [],
                    isNullable: false,
                    isList: false,
                    isSelector: false
                  }
                ],
                isList: false,
                isNullable: true,
                isSelector: false
              }
            }
          }
        ],
        loggers: [
          {
            __typename: "Logger",
            name: "console",
            description: "The default colored console logger.",
            configField: {
              __typename: "ConfigTypeField",
              configType: {
                __typename: "CompositeConfigType",
                key: "Dict.23",
                name: null,
                description: "A configuration dictionary with typed fields",
                fields: [
                  {
                    __typename: "ConfigTypeField",
                    name: "log_level",
                    description: null,
                    configType: {
                      __typename: "RegularConfigType",
                      key: "String"
                    },
                    isOptional: true
                  },
                  {
                    __typename: "ConfigTypeField",
                    name: "name",
                    description: null,
                    configType: {
                      __typename: "RegularConfigType",
                      key: "String"
                    },
                    isOptional: true
                  }
                ],
                innerTypes: [
                  {
                    __typename: "RegularConfigType",
                    name: "String",
                    key: "String",
                    description: "",
                    isList: false,
                    isNullable: false,
                    isSelector: false,
                    innerTypes: []
                  }
                ],
                isNullable: false,
                isList: false,
                isSelector: false
              }
            }
          }
        ]
      }
    ]
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <SidebarPipelineInfo pipeline={sidebarPipelineInfoData} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});
