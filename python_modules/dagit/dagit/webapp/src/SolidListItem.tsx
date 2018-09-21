import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Link } from "react-router-dom";
import { Text, Code, Card } from "@blueprintjs/core";
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
        definition {
          description
        }
        ...SolidTypeSignatureFragment
      }

      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
    `
  };

  render() {
    return (
      <SolidCard elevation={1}>
        <Link to={`/${this.props.pipelineName}/${this.props.solid.name}`}>
          <TitleCode>{this.props.solid.name}</TitleCode>
        </Link>
        <SolidTypeSignatureWrapper>
          <SolidTypeSignature solid={this.props.solid} />
        </SolidTypeSignatureWrapper>
        <DescriptionWrapper>
          <Description description={this.props.solid.definition.description} />
        </DescriptionWrapper>
      </SolidCard>
    );
  }
}

const TitleCode = styled.h3`
  font-family: "Source Code Pro", monospace;
  margin-top: 0;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const SolidCard = styled(Card)`
  position: relative;
  &&&& {
    margin-bottom: 10px;
  }
`;

const DescriptionWrapper = styled.div`
  margin-top: 5px;
  margin-bottom: 5px;
  max-width: 500px;
`;

const SolidTypeSignatureWrapper = styled.div`
  margin-bottom: 20px;
`;
