import * as React from 'react';
import styled, {css} from 'styled-components';

import {Box} from 'src/ui/Box';
import {AlignItems, FlexProperties, Spacing} from 'src/ui/types';

type Direction = 'horizontal' | 'vertical';

interface Props {
  alignItems?: AlignItems;
  background?: string;
  direction: Direction;
  margin?: Spacing;
  padding?: Spacing;
  spacing: Spacing;
}

const flexDirection = (direction: Direction) => (direction === 'horizontal' ? 'row' : 'column');
const childMargin = (direction: Direction, spacing: Spacing) =>
  direction === 'horizontal' ? {left: spacing} : {top: spacing};

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
    <Box {...rest}>
      <Inner flex={flex} direction={direction} spacing={spacing}>
        {wrappedChildren}
      </Inner>
    </Box>
  );
};

type GroupChildProps = {
  empty: boolean;
};

const GroupChild = styled(({empty, ...rest}) => <Box {...rest} />)<GroupChildProps>`
  ${({empty}) => (empty ? 'display: none;' : '')}
`;

type InnerProps = {
  direction: Direction;
  spacing: Spacing;
};

const marginAdjustment = (props: InnerProps) => {
  const {direction, spacing} = props;
  return direction === 'horizontal'
    ? css`
        margin-left: -${spacing}px;
      `
    : css`
        margin-top: -${spacing}px;
      `;
};

const Inner = styled(({direction, spacing, ...rest}) => <Box {...rest} />)<InnerProps>`
  ${marginAdjustment}

  > div:empty {
    display: none;
  }
`;
