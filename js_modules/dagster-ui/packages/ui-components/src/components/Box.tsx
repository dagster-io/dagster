import styled, {css} from 'styled-components';

import {colorKeylineDefault} from '../theme/color';
import {assertUnreachable} from '../util/assertUnreachable';

import {BorderSetting, BorderSide, DirectionalSpacing, FlexProperties} from './types';

interface Props {
  background?: string | null;
  border?: BorderSide | BorderSetting | null;
  flex?: FlexProperties | null;
  margin?: DirectionalSpacing | null;
  padding?: DirectionalSpacing | null;
}

const flexPropertiesToCSS = (flex: FlexProperties) => {
  return css`
    display: ${flex.display || 'flex'};
    ${flex.alignItems ? `align-items: ${flex.alignItems};` : null}
    ${flex.basis ? `flex-basis: ${flex.basis};` : null}
    ${flex.direction ? `flex-direction: ${flex.direction};` : null}
    ${flex.justifyContent ? `justify-content: ${flex.justifyContent};` : null}
    ${flex.grow ? `flex-grow: ${flex.grow};` : null}
    ${flex.wrap ? `flex-wrap: ${flex.wrap};` : null}
    ${flex.gap ? `gap: ${flex.gap}px;` : null}
    ${flex.shrink !== null && flex.shrink !== undefined ? `flex-shrink: ${flex.shrink};` : null}
  `;
};

const backgroundColor = (background: string) => {
  return css`
    background-color: ${background};
  `;
};

const directionalSpacingToCSS = (property: string, spacing: DirectionalSpacing) => {
  if (typeof spacing === 'number') {
    return css`
      ${property}: ${spacing}px;
    `;
  }
  const top = spacing.vertical || spacing.top || 0;
  const right = spacing.horizontal || spacing.right || 0;
  const bottom = spacing.vertical || spacing.bottom || 0;
  const left = spacing.horizontal || spacing.left || 0;
  return css`
    ${property}: ${top}px ${right}px ${bottom}px ${left}px;
  `;
};

const borderSettingToCSS = (border: BorderSide | BorderSetting) => {
  const borderValue =
    typeof border === 'string' ? {side: border, width: 1, color: colorKeylineDefault()} : border;
  const {side, width = 1, color = colorKeylineDefault()} = borderValue;

  switch (side) {
    case 'all':
      return css`
        box-shadow: inset 0 0 0 ${width}px ${color};
      `;
    case 'top-and-bottom':
      return css`
        box-shadow:
          inset 0 ${width}px ${color},
          inset 0 -${width}px ${color};
      `;
    case 'left-and-right':
      return css`
        box-shadow:
          inset ${width}px 0 ${color},
          inset -${width}px 0 ${color};
      `;
    case 'top':
      return css`
        box-shadow: inset 0 ${width}px ${color};
      `;
    case 'bottom':
      return css`
        box-shadow: inset 0 -${width}px ${color};
      `;
    case 'right':
      return css`
        box-shadow: inset -${width}px 0 ${color};
      `;
    case 'left':
      return css`
        box-shadow: inset ${width}px 0 ${color};
      `;
    default:
      assertUnreachable(side);
      return '';
  }
};

export const Box = styled.div<Props>`
  ${({flex}) => (flex ? flexPropertiesToCSS(flex) : null)}
  ${({background}) => (background ? backgroundColor(background) : null)}
  ${({margin}) => (margin ? directionalSpacingToCSS('margin', margin) : null)}
  ${({padding}) => (padding ? directionalSpacingToCSS('padding', padding) : null)}
  ${({border}) => (border ? borderSettingToCSS(border) : null)}
`;
