import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Text, Code } from "@blueprintjs/core";
import SolidTypeSignature from "./SolidTypeSignature";
import Description from "./Description";
import { SolidListItemFragment } from "./types/SolidListItemFragment";

interface ISolidListItemProps {
  pipelineName: string;
  solid: SolidListItemFragment;
}

export default class SolidListItem extends React.Component<
  ISolidListItemProps,
  {}
> {
  static fragments = {
    SolidListItemFragment: gql`
      fragment SolidListItemFragment on Solid {
        name
        description
        ...SolidTypeSignatureFragment
      }

      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
    `
  };

  render() {
    return (
      <ListItem>
        <Link to={`/${this.props.pipelineName}/${this.props.solid.name}`}>
          <Code>{this.props.solid.name}</Code>
        </Link>
        <SolidTypeSignatureWrapper>
          <SolidTypeSignature solid={this.props.solid} />
        </SolidTypeSignatureWrapper>
        <DescriptionWrapper>
          <Description description={this.props.solid.description} />
        </DescriptionWrapper>
      </ListItem>
    );
  }
}

const ListItem = styled.li`
  &&&& {
    margin-bottom: 10px;
  }
`;

const DescriptionWrapper = styled.div`
  margin-top: 5px;
  margin-bottom: 5px;
  max-width: 500px;
`;

const SolidTypeSignatureWrapper = styled.span`
  margin-left: 10px;
`;
