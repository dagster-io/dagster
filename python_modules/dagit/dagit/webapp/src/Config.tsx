import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import TypeWithTooltip from "./TypeWithTooltip";
import { ConfigFragment } from "./types/ConfigFragment";
import { TypeInfoFragment } from "./types/TypeInfoFragment";

interface ConfigProps {
  config: ConfigFragment;
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
            {fieldData.description && (
              <DictComment>{`${innerIndent}/* ${
                fieldData.description
              } */`}</DictComment>
            )}
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

export default class Config extends React.Component<ConfigProps, {}> {
  static fragments = {
    ConfigFragment: gql`
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

      fragment ConfigFragment on Config {
        type {
          ...TypeInfoFragment
          innerTypes {
            ...TypeInfoFragment
          }
        }
      }
      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  public render() {
    const { type } = this.props.config;

    const innerTypeLookup = {};
    for (const innerTypeData of type.innerTypes) {
      innerTypeLookup[innerTypeData.name] = innerTypeData;
    }

    return (
      <ConfigWrapper>
        {renderTypeRecursive(type, innerTypeLookup)}
      </ConfigWrapper>
    );
  }
}

const ConfigWrapper = styled.code`
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
  text-indent: -3em;
  padding-left: 3em;
`;

const Optional = (
  <span style={{ fontWeight: 500, color: Colors.ORANGE2 }}>?</span>
);
