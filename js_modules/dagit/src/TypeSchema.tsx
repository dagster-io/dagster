import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import TypeWithTooltip from "./TypeWithTooltip";
import { TypeSchemaFragment } from "./types/TypeSchemaFragment";
import { TypeInfoFragment } from "./types/TypeInfoFragment";

interface ITypeSchemaProps {
  type: TypeSchemaFragment;
}

function renderTypeRecursive(
  type: TypeInfoFragment,
  typeLookup: { [typeName: string]: TypeInfoFragment },
  indent: string = ""
): React.ReactElement<HTMLElement> {
  if (type.isDict && "fields" in type) {
    const innerIndent = indent + "  ";
    return (
      <>
        {`{`}
        {type.fields.map(fieldData => (
          <DictEntry key={fieldData.name}>
            <DictBlockComment
              indent={innerIndent}
              content={fieldData.description}
            />
            {innerIndent}
            <DictKey>{fieldData.name}</DictKey>
            {fieldData.isOptional && Optional}
            {`: `}
            {renderTypeRecursive(
              typeLookup[fieldData.type.name],
              typeLookup,
              innerIndent
            )}
          </DictEntry>
        ))}
        {`${indent}}`}
      </>
    );
  }
  if (type.isList) {
    const innerType = type.innerTypes[0].name;
    return (
      <>[{renderTypeRecursive(typeLookup[innerType], typeLookup, indent)}]</>
    );
  }
  if (type.isNullable) {
    const innerType = type.innerTypes[0].name;
    return (
      <>
        {renderTypeRecursive(typeLookup[innerType], typeLookup, indent)}
        {Optional}
      </>
    );
  }
  return <TypeWithTooltip type={type} />;
}

export default class TypeSchema extends React.Component<ITypeSchemaProps> {
  static fragments = {
    TypeSchemaFragment: gql`
      fragment TypeInfoFragment on Type {
        name
        description
        isDict
        isList
        isNullable
        innerTypes {
          name
        }
        ... on CompositeType {
          fields {
            name
            description
            type {
              name
            }
            isOptional
          }
        }
        ...TypeWithTooltipFragment
      }

      fragment TypeSchemaFragment on Type {
        ...TypeInfoFragment
        innerTypes {
          ...TypeInfoFragment
        }
      }
      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  public render() {
    const { type } = this.props;

    const innerTypeLookup = {};
    for (const innerTypeData of type.innerTypes) {
      innerTypeLookup[innerTypeData.name] = innerTypeData;
    }

    return (
      <TypeSchemaContainer>
        <DictBlockComment content={type.description} indent="" />
        {renderTypeRecursive(type, innerTypeLookup)}
      </TypeSchemaContainer>
    );
  }
}

const TypeSchemaContainer = styled.code`
  color: ${Colors.GRAY3};
  display: block;
  white-space: pre-wrap;
  font-size: smaller;
  line-height: 18px;
`;

const DictEntry = styled.div``;

const DictKey = styled.span`
  color: ${Colors.BLACK};
`;

const DictComment = styled.div`
  /* This allows long comments to wrap as nice indented blocks, while
     copy/pasting as a single line with space-based indentation. */
  text-indent: -1.85em;
  padding-left: 1.85em;
  white-space: initial;
`;

const DictBlockComment = ({
  indent = "",
  content
}: {
  indent: string;
  content: string | null;
}) =>
  content != null ? (
    <DictComment>{`${indent.replace(
      / /g,
      "\u00A0"
    )}/* ${content} */`}</DictComment>
  ) : null;

const Optional = (
  <span style={{ fontWeight: 500, color: Colors.ORANGE2 }}>?</span>
);
