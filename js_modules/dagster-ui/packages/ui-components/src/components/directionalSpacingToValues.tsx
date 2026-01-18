import {DirectionalSpacing} from './types';

type SpacingValues = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export const directionalSpacingToValues = (spacing: DirectionalSpacing): SpacingValues => {
  if (typeof spacing === 'number') {
    return {top: spacing, right: spacing, bottom: spacing, left: spacing};
  }

  const top = spacing.vertical || spacing.top || 0;
  const right = spacing.horizontal || spacing.right || 0;
  const bottom = spacing.vertical || spacing.bottom || 0;
  const left = spacing.horizontal || spacing.left || 0;
  return {top, right, bottom, left};
};
