import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import TypeSchema from "../TypeSchema";

it("renders given a basic type", () => {
  let intConfigData = {
    type: {
      name: "Int",
      description: "An int",
      typeAttributes: {
        isNamed: true
      },
      isDict: false,
      isList: false,
      isNullable: false,
      innerTypes: []
    }
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <TypeSchema type={intConfigData.type} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});

it("renders given a complex type", () => {
  let complexConfigData = {
    type: {
      name: "Dict.4",
      description: "",
      isDict: true,
      typeAttributes: { isNamed: false },
      isList: false,
      isNullable: false,
      fields: [
        {
          name: "field_one",
          type: {
            name: "String"
          },
          isOptional: false
        },
        {
          name: "field_two",
          type: {
            name: "String"
          },
          isOptional: false
        },
        {
          name: "field_three",
          type: {
            name: "String"
          },
          isOptional: false
        },
        {
          name: "nested_field",
          type: {
            name: "Dict.3"
          },
          isOptional: false
        }
      ],
      innerTypes: [
        {
          name: "String",
          description: "",
          isDict: false,
          isList: false,
          typeAttributes: { isNamed: true },
          isNullable: false,
          innerTypes: []
        },
        {
          name: "Dict.3",
          description: "",
          isDict: true,
          isList: false,
          typeAttributes: { isNamed: false },
          isNullable: false,
          innerTypes: [
            {
              name: "String"
            },
            {
              name: "Int"
            },
            {
              name: "List.Nullable.Int"
            },
            {
              name: "Nullable.Int"
            }
          ],
          fields: [
            {
              name: "field_four_str",
              type: {
                name: "String"
              },
              isOptional: false
            },
            {
              name: "field_five_int",
              type: {
                name: "Int"
              },
              isOptional: false
            },
            {
              name: "field_six_nullable_int_list",
              type: {
                name: "List.Nullable.Int"
              },
              isOptional: true
            }
          ]
        },
        {
          name: "Int",
          description: "",
          isDict: false,
          isList: false,
          typeAttributes: { isNamed: true },
          isNullable: false,
          innerTypes: []
        },
        {
          name: "List.Nullable.Int",
          description: "",
          isDict: false,
          isList: true,
          typeAttributes: { isNamed: false },
          isNullable: false,
          innerTypes: [
            {
              name: "Nullable.Int"
            },
            {
              name: "Int"
            }
          ]
        },
        {
          name: "Nullable.Int",
          description: "",
          isDict: false,
          isList: false,
          typeAttributes: { isNamed: false },
          isNullable: true,
          innerTypes: [
            {
              name: "Int"
            }
          ]
        }
      ]
    }
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <TypeSchema type={complexConfigData.type} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});
