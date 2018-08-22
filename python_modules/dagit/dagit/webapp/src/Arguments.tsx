import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { H5, H6, Text, UL, Code, Collapse } from "@blueprintjs/core";
import SpacedCard from "./SpacedCard";
import TypeWithTooltip from "./TypeWithTooltip";
import Description from "./Description";
import { ArgumentsFragment } from "./types/ArgumentsFragment";

interface ArgumentsProps {
  arguments: Array<ArgumentsFragment>;
}

export default class Arguments extends React.Component<ArgumentsProps, {}> {
  static fragments = {
    ArgumentsFragment: gql`
      fragment ArgumentsFragment on Argument {
        name
        description
        type {
          ...TypeFragment
        }
        isOptional
      }

      ${TypeWithTooltip.fragments.TypeFragment}
    `
  };

  public render() {
    return (
      <UL>
        {this.props.arguments.map((argument: any, i: number) => (
          <li key={i}>
            {argument.name} {argument.isOptional ? "(optional)" : null}{" "}
            <TypeWithTooltip type={argument.type} />
            <DescriptionWrapper>
              <Description description={argument.description} />
            </DescriptionWrapper>
          </li>
        ))}
      </UL>
    );
  }
}

const DescriptionWrapper = styled.div`
  max-width: 400px;
  margin-bottom: 10px;
`;
