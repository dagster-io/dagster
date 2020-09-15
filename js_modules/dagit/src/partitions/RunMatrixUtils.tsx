import styled from 'styled-components/macro';
import {Colors} from '@blueprintjs/core';
import {RUN_STATUS_COLORS} from '../runs/RunStatusDots';

const SUCCESS_COLOR = ({dimSuccesses}: {dimSuccesses?: boolean}) =>
  dimSuccesses ? '#CFE6DC' : '#009857';
// In CSS, you can layer multiple backgrounds on top of each other by comma-separating values in
// `background`. However, this only works with gradients, not with primitive color values. To do
// hovered + red without color math (?), just stack the colors as flat gradients.
const flatGradient = (color: string) => `linear-gradient(to left, ${color} 0%, ${color} 100%)`;
const flatGradientStack = (colors: string[]) => colors.map(flatGradient).join(',');

export const GridColumn = styled.div<{
  disabled?: boolean;
  focused?: boolean;
  multiselectFocused?: boolean;
  dimSuccesses?: boolean;
}>`
  display: flex;
  flex-direction: column;
  flex-shrink: 0;

  ${({disabled, focused, multiselectFocused}) =>
    !disabled &&
    !focused &&
    !multiselectFocused &&
    `&:hover {
    cursor: default;
    background: ${Colors.LIGHT_GRAY3};
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      .tilted {
        background: ${Colors.LIGHT_GRAY3};
      }
    }
  }`}

  ${({disabled}) =>
    disabled &&
    `
      ${TopLabelTilted} {
        color: ${Colors.GRAY3}
      }
    `}

  ${({focused}) =>
    focused &&
    `background: ${Colors.BLUE4};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      color: white;
      .tilted {
        background: ${Colors.BLUE4};
      }
    }
  }`}

  ${({multiselectFocused}) =>
    multiselectFocused &&
    `background: ${Colors.BLUE5};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTilted} {
      background: ${Colors.LIGHT_GRAY5};
      color: white;
      .tilted {
        background: ${Colors.BLUE5};
      }
    }
  }`}

  .square {
    width: 23px;
    height: 23px;
    display: inline-block;

    &:before {
      content: ' ';
      display: inline-block;
      width: 15px;
      height: 15px;
      margin: 4px;
    }
    &.success {
      &:before {
        background: ${SUCCESS_COLOR};
      }
    }
    &.failure {
      &:before {
        background: ${RUN_STATUS_COLORS.FAILURE};
      }
    }
    &.failure-success {
      &:before {
        background: linear-gradient(135deg, ${RUN_STATUS_COLORS.FAILURE} 40%, ${SUCCESS_COLOR} 41%);
      }
    }
    &.failure-blank {
      &:before {
        background: linear-gradient(
          135deg,
          ${RUN_STATUS_COLORS.FAILURE} 40%,
          rgba(150, 150, 150, 0.3) 41%
        );
      }
    }
    &.skipped {
      &:before {
        background: ${Colors.GOLD3};
      }
    }
    &.skipped-success {
      &:before {
        background: linear-gradient(135deg, ${Colors.GOLD3} 40%, ${SUCCESS_COLOR} 41%);
      }
    }
    &.missing {
      &:before {
        background: ${Colors.WHITE};
      }
    }
    &.missing-success {
      &:before {
        background: linear-gradient(135deg, ${Colors.WHITE} 40%, ${SUCCESS_COLOR} 41%);
      }
    }
  }
`;

export const LeftLabel = styled.div<{hovered?: boolean; redness?: number}>`
  height: 23px;
  line-height: 23px;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  background: ${({redness, hovered}) =>
    flatGradientStack([
      redness ? `rgba(255, 0, 0, ${redness * 0.6})` : 'transparent',
      hovered ? Colors.LIGHT_GRAY3 : 'transparent',
    ])};
`;

export const TopLabel = styled.div`
  position: relative;
  height: 70px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  align-items: flex-end;
  display: flex;
`;

export const TopLabelTilted = styled.div`
  position: relative;
  height: 55px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  margin-bottom: 15px;
  align-items: end;
  display: flex;

  & > div.tilted {
    font-size: 12px;
    white-space: nowrap;
    position: absolute;
    bottom: -20px;
    left: 0;
    padding: 2px;
    padding-right: 4px;
    padding-left: 0;
    transform: rotate(-41deg);
    transform-origin: top left;
  }
`;

export const GridFloatingContainer = styled.div<{floating: boolean}>`
  display: flex;
  border-right: 1px solid ${Colors.GRAY5};
  padding-bottom: 16px;
  width: 330px;
  z-index: 2;
  ${({floating}) => (floating ? 'box-shadow: 1px 0 4px rgba(0, 0, 0, 0.15)' : '')};
`;

export const GridScrollContainer = styled.div`
  padding-right: 60px;
  padding-bottom: 16px;
  overflow-x: scroll;
  z-index: 0;
  background: ${Colors.LIGHT_GRAY5};
  flex: 1;
`;
