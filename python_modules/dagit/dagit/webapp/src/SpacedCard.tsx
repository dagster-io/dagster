import * as React from "react";
import styled, { css } from "styled-components";
import { Card, ICardProps } from "@blueprintjs/core";

interface ISpacedCardProps {
  horizontal?: boolean;
}

const determineMargin = (props: ISpacedCardProps) =>
  props.horizontal ? horizontal : vertical;

const horizontal = css`
  margin-right: 10px;

  &:last-child {
    margin-right: 0;
  }
`;
const vertical = css`
  margin-bottom: 10px;

  &:last-child {
    margin-bottom: 0;
  }
`;

const SpacedCard = styled(Card)`
  ${determineMargin};
`;

export default SpacedCard;
