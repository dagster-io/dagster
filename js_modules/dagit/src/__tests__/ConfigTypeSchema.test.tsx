import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import ConfigTypeSchema from "../ConfigTypeSchema";

it("renders given a basic type", () => {
  let intConfigData = {
    configType: {
      key: "Int",
      name: "Int",
      description: "An int",
      typeAttributes: {
        isNamed: true
      },
      isList: false,
      isSelector: false,
      isNullable: false,
      innerTypes: []
    }
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <ConfigTypeSchema type={intConfigData.configType} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});

it("renders given a complex type", () => {
  let complexConfigData = {
    configType: {
      key: "Dict.4",
      name: "Dict.4",
      description: "",
      typeAttributes: { isNamed: false },
      isList: false,
      isSelector: false,
      isNullable: false,
      fields: [
        {
          name: "field_one",
          configType: {
            key: "String",
            name: "String"
          },
          isOptional: false
        },
        {
          name: "field_two",
          configType: {
            key: "String",
            name: "String"
          },
          isOptional: false
        },
        {
          name: "field_three",
          configType: {
            key: "String",
            name: "String"
          },
          isOptional: false
        },
        {
          name: "nested_field",
          configType: {
            key: "Dict.3",
            name: "Dict.3"
          },
          isOptional: false
        }
      ],
      innerTypes: [
        {
          key: "String",
          name: "String",
          description: "",
          isList: false,
          typeAttributes: { isNamed: true },
          isSelector: false,
          isNullable: false,
          innerTypes: []
        },
        {
          key: "Dict.3",
          name: "Dict.3",
          description: "",
          isList: false,
          typeAttributes: { isNamed: false },
          isSelector: false,
          isNullable: false,
          innerTypes: [
            {
              key: "String",
              name: "String"
            },
            {
              key: "Int",
              name: "Int"
            },
            {
              key: "List.Nullable.Int",
              name: "List.Nullable.Int"
            },
            {
              key: "Nullable.Int",
              name: "Nullable.Int"
            }
          ],
          fields: [
            {
              name: "field_four_str",
              configType: {
                key: "String",
                name: "String"
              },
              isOptional: false
            },
            {
              name: "field_five_int",
              configType: {
                key: "Int",
                name: "Int"
              },
              isOptional: false
            },
            {
              name: "field_six_nullable_int_list",
              configType: {
                key: "List.Nullable.Int",
                name: "List.Nullable.Int"
              },
              isOptional: true
            }
          ]
        },
        {
          key: "Int",
          name: "Int",
          description: "",
          isList: false,
          typeAttributes: { isNamed: true },
          isSelector: false,
          isNullable: false,
          innerTypes: []
        },
        {
          key: "List.Nullable.Int",
          name: "List.Nullable.Int",
          description: "",
          isList: true,
          typeAttributes: { isNamed: false },
          isSelector: false,
          isNullable: false,
          innerTypes: [
            {
              key: "Nullable.Int",
              name: "Nullable.Int"
            },
            {
              key: "Int",
              name: "Int"
            }
          ]
        },
        {
          key: "Nullable.Int",
          name: "Nullable.Int",
          description: "",
          isList: false,
          typeAttributes: { isNamed: false },
          isSelector: false,
          isNullable: true,
          innerTypes: [
            {
              key: "Int",
              name: "Int"
            }
          ]
        }
      ]
    }
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <ConfigTypeSchema type={complexConfigData.configType} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});
