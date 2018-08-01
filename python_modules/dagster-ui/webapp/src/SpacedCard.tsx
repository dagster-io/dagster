import * as React from "react";
import styled, { css } from "styled-components";
import { Card, ICardProps } from "@blueprintjs/core";

interface ISpacedCardProps {
  horizontal?: boolean;
}

const determineMargin = (props: ISpacedCardProps) =>
  props.horizontal ? horizontal : vertical;

const horizontal = css`
  margin-left: 10px;
`;
const vertical = css`
  margin-top: 10px;
`;

const SpacedCard = styled(Card)`
  ${determineMargin};
`;

export default SpacedCard;
