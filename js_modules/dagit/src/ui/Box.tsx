import styled, {css} from 'styled-components';

import {assertUnreachable} from 'src/Util';
import {BorderColor, BorderSetting, DirectionalSpacing, FlexProperties} from 'src/ui/types';

export interface Props {
  background?: string;
  border?: BorderSetting;
  flex?: FlexProperties;
  margin?: DirectionalSpacing;
  padding?: DirectionalSpacing;
}

const flexPropertiesToCSS = (flex: FlexProperties) => {
  return css`
    display: ${flex.display || 'flex'};
    ${flex.alignItems ? `align-items: ${flex.alignItems};` : null}
    ${flex.basis ? `flex-basis: ${flex.basis};` : null}
    ${flex.direction
      ? `flex-direction: ${flex.direction};`
      : null}
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

const borderColor = (color: BorderColor) => {
  switch (color) {
    case 'light':
      return 'rgba(0, 0, 0, 0.1)';
    case 'medium':
      return 'rgba(0, 0, 0, 0.2)';
    case 'dark':
      return 'rgba(0, 0, 0, 0.4)';
    default:
      assertUnreachable(color);
  }
};

const borderSettingToCSS = (border: BorderSetting) => {
  const {side, width, color} = border;
  const shadowColor = borderColor(color);
  switch (side) {
    case 'all':
      return css`
        box-shadow: inset 0 0 0 ${width}px ${shadowColor};
      `;
    case 'horizontal':
      return css`
        box-shadow: inset 0 ${width}px ${shadowColor}, inset 0 -${width}px ${shadowColor};
      `;
    case 'vertical':
      return css`
        box-shadow: inset ${width}px 0 ${shadowColor}, inset -${width}px 0 ${shadowColor};
      `;
    case 'top':
      return css`
        box-shadow: inset 0 ${width}px ${shadowColor};
      `;
    case 'bottom':
      return css`
        box-shadow: inset 0 -${width}px ${shadowColor};
      `;
    case 'right':
      return css`
        box-shadow: inset -${width}px 0 ${shadowColor};
      `;
    case 'left':
      return css`
        box-shadow: inset ${width}px 0 ${shadowColor};
      `;
    default:
      assertUnreachable(side);
  }
};

export const Box = styled.div<Props>`
  ${({flex}) => (flex ? flexPropertiesToCSS(flex) : null)}
  ${({background}) => (background ? backgroundColor(background) : null)}
  ${({margin}) =>
    margin ? directionalSpacingToCSS('margin', margin) : null}
  ${({padding}) =>
    padding ? directionalSpacingToCSS('padding', padding) : null}
  ${({border}) =>
    border ? borderSettingToCSS(border) : null}
`;
