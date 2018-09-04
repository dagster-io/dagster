import * as React from "react";
import styled, { css } from "styled-components";
import { Card, ICardProps } from "@blueprintjs/core";

type ISpacedCardProps = ICardProps & {
  horizontal?: boolean;
};

export default class SpacedCard extends React.Component<ISpacedCardProps> {
  render() {
    const { horizontal, ...rest } = this.props;
    if (horizontal) {
      return <HorizontalCard {...rest}>{this.props.children}</HorizontalCard>;
    } else {
      return <VerticalCard {...rest}>{this.props.children}</VerticalCard>;
    }
  }
}

const HorizontalCard = styled(Card)`
  margin-right: 10px;

  &:last-child {
    margin-right: 0;
  }
`;

const VerticalCard = styled(Card)`
  margin-bottom: 10px;

  &:last-child {
    margin-bottom: 0;
  }
`;
