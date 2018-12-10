import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { UL, Colors } from "@blueprintjs/core";
import TypeWithTooltip from "./TypeWithTooltip";
import Description from "./Description";
import { ConfigFragment } from "./types/ConfigFragment";

interface ConfigProps {
  config: ConfigFragment;
}

export default class Config extends React.Component<ConfigProps, {}> {
  static fragments = {
    ConfigFragment: gql`
      fragment ConfigFragment on Config {
        type {
          __typename
          name
          description
          ... on CompositeType {
            fields {
              name
              description
              isOptional
              defaultValue
              type {
                name
                description
                ...TypeWithTooltipFragment
                ... on CompositeType {
                  fields {
                    name
                    description
                    isOptional
                    defaultValue
                    type {
                      name
                      description
                      ...TypeWithTooltipFragment
                    }
                  }
                }
              }
            }
          }
          ...TypeWithTooltipFragment
        }
      }

      ${TypeWithTooltip.fragments.TypeWithTooltipFragment}
    `
  };

  renderFields(config: ConfigFragment) {
    if (config.type.__typename === "CompositeType") {
      return (
        <UL>
          {config.type.fields.map((field, i: number) => (
            <li key={i}>
              {field.name} {field.isOptional ? "(optional)" : null}{" "}
              <TypeWithTooltip type={field.type} />
              <DescriptionWrapper>
                <Description description={field.description} />
              </DescriptionWrapper>
            </li>
          ))}
        </UL>
      );
    } else {
      return null;
    }
  }

  public render() {
    return (
      <div>
        <TypeWithTooltip type={this.props.config.type} />
        {this.renderFields(this.props.config)}
      </div>
    );
  }
}

const DescriptionWrapper = styled.div`
  margin-top: 10px;
  margin-bottom: 10px;
  color: ${Colors.GRAY2};
`;
