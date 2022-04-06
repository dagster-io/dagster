import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

export const BOX_SIZE = 32;

export const STEP_STATUS_COLORS = {
  SUCCESS: Colors.Green500,
  FAILURE: Colors.Red500,
  SKIPPED: Colors.Yellow500,
  IN_PROGRESS: '#eee',
};

// In CSS, you can layer multiple backgrounds on top of each other by comma-separating values in
// `background`. However, this only works with gradients, not with primitive color values. To do
// hovered + red without color math (?), just stack the colors as flat gradients.
const flatGradient = (color: string) => `linear-gradient(to left, ${color} 0%, ${color} 100%)`;
const flatGradientStack = (colors: string[]) => colors.map(flatGradient).join(',');

export const GridColumn = styled.div<{
  disabled?: boolean;
  hovered?: boolean;
  focused?: boolean;
  multiselectFocused?: boolean;
}>`
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  line-height: 0;

  ${({disabled, focused, multiselectFocused, hovered}) =>
    !disabled &&
    !focused &&
    !multiselectFocused &&
    `&${hovered ? '' : ':hover'} {
      background: ${Colors.Gray100};
      cursor: default;
      ${TopLabelTiltedInner} {
        background: ${Colors.White};
        .tilted {
          background: ${Colors.Gray100};
        }
      }
      .square {
        filter: brightness(95%);
      }
    }`}

  ${({disabled}) =>
    disabled &&
    `
      ${TopLabelTiltedInner} {
        color: ${Colors.Gray400}
      }
    `}

  ${({focused}) =>
    focused &&
    `background: ${Colors.Blue500};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTiltedInner} {
      background: ${Colors.White};
      color: white;
      .tilted {
        background: ${Colors.Blue500};
      }
    }
  }`}

  ${({multiselectFocused}) =>
    multiselectFocused &&
    `background: ${Colors.Blue200};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTiltedInner} {
      background: ${Colors.White};
      color: white;
      .tilted {
        background: ${Colors.Blue200};
      }
    }
  }`}

  .cell {
    height: ${BOX_SIZE}px;
    display: inline-block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 12px;
    padding: 2px;
    box-sizing: border-box;
    line-height: initial;
  }

  .square {
    width: 20px;
    height: 20px;
    margin: 6px;
    display: inline-block;

    &:hover:not(.empty):before {
      box-shadow: ${Colors.Blue500} 0 0 0 3px;
    }
    &:before {
      content: ' ';
      background: rgba(248, 247, 245, 1);
      border-radius: 10px;
      display: inline-block;
      width: 20px;
      height: 20px;
    }
    &.loading {
      &:before {
        background: radial-gradient(white 0%, white 45%, rgba(248, 247, 245, 1) 60%);
      }
    }
    &.success {
      &:before {
        background: ${STEP_STATUS_COLORS.SUCCESS};
      }
    }
    &.success-skipped {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SUCCESS} 49%,
          ${STEP_STATUS_COLORS.SKIPPED} 51%
        );
      }
    }
    &.success-failure {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SUCCESS} 49%,
          ${STEP_STATUS_COLORS.FAILURE} 51%
        );
      }
    }
    &.failure {
      &:before {
        background: ${STEP_STATUS_COLORS.FAILURE};
      }
    }
    &.failure-success {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 49%,
          ${STEP_STATUS_COLORS.SUCCESS} 51%
        );
      }
    }
    &.failure-skipped {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 49%,
          ${STEP_STATUS_COLORS.SKIPPED} 51%
        );
      }
    }
    &.failure-blank {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 49%,
          rgba(150, 150, 150, 0.3) 51%
        );
      }
    }
    &.skipped {
      &:before {
        background: ${STEP_STATUS_COLORS.SKIPPED};
      }
    }
    &.skipped-success {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SKIPPED} 49%,
          ${STEP_STATUS_COLORS.SUCCESS} 51%
        );
      }
    }
    &.skipped-failure {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SKIPPED} 49%,
          ${STEP_STATUS_COLORS.FAILURE} 51%
        );
      }
    }
  }
`;

export const LeftLabel = styled.div<{hovered?: boolean}>`
  height: ${BOX_SIZE}px;
  line-height: ${BOX_SIZE}px;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  background: ${({hovered}) => flatGradientStack([hovered ? Colors.Gray100 : 'transparent'])};
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

const TITLE_MARGIN_BOTTOM = 15;
const ROTATION_DEGREES = 41;

export function topLabelHeightForLabels(labels: string[]) {
  const maxlength = Math.max(...labels.map((p) => p.length));
  return (maxlength > 10 ? maxlength * 4.9 : 55) + TITLE_MARGIN_BOTTOM;
}

export const TopLabelTilted: React.FC<{label: string; $height: number}> = ({label, $height}) => {
  return (
    <TopLabelTiltedInner style={{height: $height - TITLE_MARGIN_BOTTOM}}>
      <div className="tilted">{label}</div>
    </TopLabelTiltedInner>
  );
};

const TopLabelTiltedInner = styled.div`
  position: relative;
  height: unset; /* provide via style tag */
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  margin-bottom: ${TITLE_MARGIN_BOTTOM}px;
  align-items: end;
  display: flex;
  line-height: normal;

  & > div.tilted {
    font-size: 12px;
    white-space: nowrap;
    position: absolute;
    bottom: -20px;
    left: 0;
    padding: 2px;
    padding-right: 4px;
    padding-left: 0;
    transform: rotate(-${ROTATION_DEGREES}deg);
    transform-origin: top left;
  }
`;

export const GridFloatingContainer = styled.div<{floating: boolean}>`
  display: flex;
  border-right: 1px solid ${Colors.Gray200};
  padding-bottom: 16px;
  width: 330px;
  z-index: 1;
  ${({floating}) => (floating ? 'box-shadow: 1px 0 4px rgba(0, 0, 0, 0.15)' : '')};
`;

export const GridScrollContainer = styled.div`
  padding-right: 60px;
  padding-bottom: 16px;
  overflow-x: scroll;
  overscroll-behavior-x: contain;
  z-index: 0;
  background: ${Colors.White};
  flex: 1;
  scrollbar-color: ${Colors.Gray500} ${Colors.Gray100};
  scrollbar-width: thin;

  ::-webkit-scrollbar {
    -webkit-appearance: none;
  }
  &::-webkit-scrollbar:vertical {
    width: 11px;
  }
  &::-webkit-scrollbar:horizontal {
    height: 11px;
  }
  &::-webkit-scrollbar-thumb {
    border-radius: 8px;
    border: 2px solid ${Colors.Gray100};
    background-color: ${Colors.Gray500};
  }
  &::-webkit-scrollbar-track {
    background-color: ${Colors.Gray100};
  }
`;
