import * as React from 'react';
import styled, {css} from 'styled-components';

import {Box} from 'src/ui/Box';
import {AlignItems, DirectionalSpacing, FlexProperties, Spacing} from 'src/ui/types';

type Direction = 'row' | 'column';

interface Props {
  alignItems?: AlignItems;
  background?: string;
  direction: Direction;
  margin?: DirectionalSpacing;
  padding?: DirectionalSpacing;
  spacing: Spacing;
}

const flexDirection = (direction: Direction) => (direction === 'row' ? 'row' : 'column');
const childMargin = (direction: Direction, spacing: Spacing) =>
  direction === 'row' ? {left: spacing} : {top: spacing};

export const Group: React.FC<Props> = (props) => {
  const {alignItems, children, direction, spacing, ...rest} = props;
  const wrappedChildren = React.Children.map(children, (child) => {
    const margin = childMargin(direction, spacing);
    return (
      <GroupChild empty={!child} margin={margin}>
        {child}
      </GroupChild>
    );
  });

  const flex: FlexProperties = {
    direction: flexDirection(direction),
  };

  if (alignItems) {
    flex.alignItems = alignItems;
  }

  return (
    <Outer {...rest}>
      <Inner flex={flex} direction={direction} spacing={spacing}>
        {wrappedChildren}
      </Inner>
    </Outer>
  );
};

type GroupChildProps = {
  empty: boolean;
};

const GroupChild = styled(({empty, ...rest}) => <Box {...rest} />)<GroupChildProps>`
  ${({empty}) => (empty ? 'display: none;' : '')}
  pointer-events: auto;
`;

type InnerProps = {
  direction: Direction;
  spacing: Spacing;
};

const marginAdjustment = (props: InnerProps) => {
  const {direction, spacing} = props;
  return direction === 'row'
    ? css`
        margin-left: -${spacing}px;
      `
    : css`
        margin-top: -${spacing}px;
      `;
};

const Outer = styled(Box)`
  pointer-events: none;
`;

const Inner = styled(({direction, spacing, ...rest}) => <Box {...rest} />)<InnerProps>`
  ${marginAdjustment}

  > div:empty {
    display: none;
  }
`;
