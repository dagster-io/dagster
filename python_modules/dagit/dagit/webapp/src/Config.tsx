import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { UL, Colors } from "@blueprintjs/core";
import TypeWithTooltip from "./TypeWithTooltip";
import Description from "./Description";
import { ConfigFragment } from "./types/ConfigFragment";
import { ConfigPipelineTypesFragment } from "./types/ConfigPipelineTypesFragment";

interface ConfigProps {
  config: ConfigFragment;
  pipeline: ConfigPipelineTypesFragment;
}

export default class Config extends React.Component<ConfigProps, {}> {
  static fragments = {
    ConfigFragment: gql`
      fragment ConfigFragment on Config {
        type {
          ...TypeWithTooltipFragment
          __typename
          name
        }
      }
      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `,
    ConfigPipelineTypesFragment: gql`
      fragment ConfigPipelineTypesFragment on Pipeline {
        types {
          __typename
          ... on CompositeType {
            fields {
              name
              description
              isOptional
              defaultValue
              type {
                __typename
                name
              }
            }
          }
          ...TypeWithTooltipFragment
        }
      }
      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  public render() {
    const {
      pipeline: { types },
      config
    } = this.props;

    let result = "{";

    const appendDict = (indent: string, typename: string) => {
      const type = types.find(t => t.name === typename);
      if (!type || type.__typename !== "CompositeType") {
        return;
      }
      type.fields.forEach(field => {
        if (field.type.__typename === "CompositeType") {
          result += `\n${indent}{`;
          appendDict(indent + "  ", field.type.name);
          result += `\n${indent}}`;
        } else {
          result += `\n${indent}${field.name}: ${field.type.name}${
            field.isOptional ? "?" : ""
          }`;
        }
      });
    };

    appendDict("  ", config.type.name);

    if (result == "{") {
      return <span />;
    }

    result += "\n}";

    return <ConfigWrapper>{result}</ConfigWrapper>;
  }
}

const ConfigWrapper = styled.code`
  margin-top: 10px;
  margin-bottom: 10px;
  color: ${Colors.BLACK};
  display: block;
  white-space: pre-wrap;
  font-size: 12px;
`;
