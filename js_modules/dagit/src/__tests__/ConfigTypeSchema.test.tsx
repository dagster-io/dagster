import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import ConfigTypeSchema from "../ConfigTypeSchema";
import { ConfigTypeSchemaFragment } from "../types/ConfigTypeSchemaFragment";

it("renders given a basic type", () => {
  const intConfigData: ConfigTypeSchemaFragment = {
    __typename: "RegularConfigType",
    key: "Int",
    name: "Int",
    description: "An int",
    isList: false,
    isSelector: false,
    isNullable: false,
    innerTypes: []
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <ConfigTypeSchema type={intConfigData} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});

it("renders given a complex type", () => {
  let complexConfigData: ConfigTypeSchemaFragment = {
    __typename: "CompositeConfigType",
    key: "Dict.4",
    name: "Dict.4",
    description: "",
    isList: false,
    isSelector: false,
    isNullable: false,
    fields: [
      {
        __typename: "ConfigTypeField",
        description: "",
        name: "field_one",
        configType: {
          __typename: "RegularConfigType",
          key: "String"
        },
        isOptional: false
      },
      {
        __typename: "ConfigTypeField",
        description: "",
        name: "field_two",
        configType: {
          __typename: "RegularConfigType",
          key: "String"
        },
        isOptional: false
      },
      {
        __typename: "ConfigTypeField",
        description: "",
        name: "field_three",
        configType: {
          __typename: "RegularConfigType",
          key: "String"
        },
        isOptional: false
      },
      {
        __typename: "ConfigTypeField",
        description: "",
        name: "nested_field",
        configType: {
          __typename: "CompositeConfigType",
          key: "Dict.3"
        },
        isOptional: false
      }
    ],
    innerTypes: [
      {
        __typename: "RegularConfigType",
        key: "String",
        name: "String",
        description: "",
        isList: false,
        isSelector: false,
        isNullable: false,
        innerTypes: []
      },
      {
        __typename: "RegularConfigType",
        key: "Dict.3",
        name: "Dict.3",
        description: "",
        isList: false,
        isSelector: false,
        isNullable: false,
        innerTypes: [
          {
            __typename: "RegularConfigType",
            key: "String"
          },
          {
            __typename: "RegularConfigType",
            key: "Int"
          },
          {
            __typename: "ListConfigType",
            key: "List.Nullable.Int"
          },
          {
            __typename: "NullableConfigType",
            key: "Nullable.Int"
          }
        ]
      },
      {
        __typename: "RegularConfigType",
        key: "Int",
        name: "Int",
        description: "",
        isList: false,
        isSelector: false,
        isNullable: false,
        innerTypes: []
      },
      {
        __typename: "ListConfigType",
        key: "List.Nullable.Int",
        name: "List.Nullable.Int",
        description: "",
        isList: true,
        isSelector: false,
        isNullable: false,
        innerTypes: [
          {
            __typename: "NullableConfigType",
            key: "Nullable.Int"
          },
          {
            __typename: "RegularConfigType",
            key: "Int"
          }
        ]
      },
      {
        __typename: "NullableConfigType",
        key: "Nullable.Int",
        name: "Nullable.Int",
        description: "",
        isList: false,
        isSelector: false,
        isNullable: true,
        innerTypes: [
          {
            __typename: "RegularConfigType",
            key: "Int"
          }
        ]
      }
    ]
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <ConfigTypeSchema type={complexConfigData} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});
