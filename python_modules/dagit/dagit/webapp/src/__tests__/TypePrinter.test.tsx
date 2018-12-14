import { printType } from "../typeexplorer/TypePrinter";

it("print int", () => {
  let intData = {
    name: "Int",
    isDict: false,
    isList: false,
    isNullable: false,
    innerTypes: []
  };
  expect(printType(intData)).toEqual("Int");
});

it("print dict", () => {
  let intData = {
    name: "Int",
    isDict: false,
    isList: false,
    isNullable: false,
    innerTypes: []
  };
  let expected = `{
  field_one: String
  field_two: String
  field_three: String
  nested_field: {
    field_four_str: String
    field_five_int: Int
    field_six_nullable_int_list?: [Int?]
  }
}`;
  expect(printType(testData.type)).toEqual(expected);
});

// See TYPE_RENDER_QUERY in test_graphql.py
let testData = {
  type: {
    name: "Dict.4",
    isDict: true,
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
        isDict: false,
        isList: false,
        isNullable: false,
        innerTypes: []
      },
      {
        name: "Dict.3",
        isDict: true,
        isList: false,
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
        isDict: false,
        isList: false,
        isNullable: false,
        innerTypes: []
      },
      {
        name: "List.Nullable.Int",
        isDict: false,
        isList: true,
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
        isDict: false,
        isList: false,
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
