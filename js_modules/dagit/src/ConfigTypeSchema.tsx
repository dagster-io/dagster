import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { ConfigTypeSchemaFragment } from "./types/ConfigTypeSchemaFragment";
import { ConfigTypeInfoFragment } from "./types/ConfigTypeInfoFragment";

type ConfigTypeSchemaTheme = "dark" | "light";

interface ConfigTypeSchemaProps {
  type: ConfigTypeSchemaFragment;
  theme?: ConfigTypeSchemaTheme;
  maxDepth?: number;
}

function renderTypeRecursive(
  type: ConfigTypeInfoFragment,
  typeLookup: { [typeName: string]: ConfigTypeInfoFragment },
  depth: number,
  props: ConfigTypeSchemaProps
): React.ReactElement<HTMLElement> {
  if ("fields" in type && props.maxDepth && depth === props.maxDepth) {
    return <span>...</span>;
  }
  if ("fields" in type) {
    const innerIndent = "  ".repeat(depth + 1);
    return (
      <>
        {`{`}
        {type.isSelector && (
          <DictBlockComment
            indent={innerIndent}
            content={`One of the following:`}
          />
        )}
        {type.fields.map(fieldData => (
          <DictEntry key={fieldData.name}>
            <DictBlockComment
              indent={innerIndent}
              content={fieldData.description}
            />
            {innerIndent}
            <DictKey theme={props.theme}>{fieldData.name}</DictKey>
            {fieldData.isOptional && Optional}
            {`: `}
            {renderTypeRecursive(
              typeLookup[fieldData.configType.key],
              typeLookup,
              depth + 1,
              props
            )}
          </DictEntry>
        ))}
        {"  ".repeat(depth) + "}"}
      </>
    );
  }
  if (type.isList) {
    const innerType = type.innerTypes[0].key;
    return (
      <>
        [{renderTypeRecursive(typeLookup[innerType], typeLookup, depth, props)}]
      </>
    );
  }
  if (type.isNullable) {
    const innerType = type.innerTypes[0].key;
    return (
      <>
        {renderTypeRecursive(typeLookup[innerType], typeLookup, depth, props)}
        {Optional}
      </>
    );
  }

  return <span>{type.name || "Anonymous Type"}</span>;
}

export default class ConfigTypeSchema extends React.Component<
  ConfigTypeSchemaProps
> {
  static fragments = {
    ConfigTypeSchemaFragment: gql`
      fragment ConfigTypeInfoFragment on ConfigType {
        key
        name
        description
        isList
        isNullable
        isSelector
        innerTypes {
          key
        }
        ... on CompositeConfigType {
          fields {
            name
            description
            isOptional
            configType {
              key
            }
          }
        }
      }

      fragment ConfigTypeSchemaFragment on ConfigType {
        ...ConfigTypeInfoFragment
        innerTypes {
          ...ConfigTypeInfoFragment
        }
      }
    `
  };

  public render() {
    const { type } = this.props;

    const innerTypeLookup = {};
    for (const innerTypeData of type.innerTypes) {
      innerTypeLookup[innerTypeData.key] = innerTypeData;
    }

    return (
      <TypeSchemaContainer>
        <DictBlockComment content={type.description} indent="" />
        {renderTypeRecursive(type, innerTypeLookup, 0, this.props)}
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

const DictKey = styled.span<{ theme: ConfigTypeSchemaTheme | undefined }>`
  color: ${({ theme }) => (theme === "dark" ? Colors.WHITE : Colors.BLACK)};
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
  content !== null && content !== "" ? (
    <DictComment>{`${indent.replace(
      / /g,
      "\u00A0"
    )}/* ${content} */`}</DictComment>
  ) : null;

const Optional = (
  <span style={{ fontWeight: 500, color: Colors.ORANGE2 }}>?</span>
);
