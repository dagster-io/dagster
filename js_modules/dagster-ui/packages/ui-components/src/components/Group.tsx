import * as React from 'react';
import styled, {css} from 'styled-components';

import {Box} from './Box';
import {AlignItems, DirectionalSpacing, FlexProperties, FlexWrap, Spacing} from './types';

type Direction = 'row' | 'column';

interface Props {
  children: React.ReactNode;
  alignItems?: AlignItems;
  background?: string;
  direction: Direction;
  margin?: DirectionalSpacing;
  padding?: DirectionalSpacing;
  spacing: Spacing;
  wrap?: FlexWrap;
}

const flexDirection = (direction: Direction) => (direction === 'row' ? 'row' : 'column');
const childMargin = (direction: Direction, spacing: Spacing) => ({left: spacing, top: spacing});

export const Group = (props: Props) => {
  const {alignItems, children, direction, spacing, wrap, ...rest} = props;
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

  if (wrap) {
    flex.wrap = wrap;
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

const GroupChild = styled(({empty: _empty, ...rest}) => <Box {...rest} />)<GroupChildProps>`
  ${({empty}) => (empty ? 'display: none;' : '')}
  pointer-events: auto;
`;

type InnerProps = {
  spacing: Spacing;
};

const marginAdjustment = (props: InnerProps) => {
  const {spacing} = props;
  return css`
    margin-left: -${spacing}px;
    margin-top: -${spacing}px;
  `;
};

const Outer = styled(Box)`
  pointer-events: none;
`;

const Inner = styled(({direction: _direction, spacing: _spacing, ...rest}) => (
  <Box {...rest} />
))<InnerProps>`
  ${marginAdjustment}

  > div:empty {
    display: none;
  }
`;
