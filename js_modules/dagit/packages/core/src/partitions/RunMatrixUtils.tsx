import {Tooltip2} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../ui/Colors';

export const STEP_STATUS_COLORS = {
  SUCCESS: '#009857',
  FAILURE: ColorsWIP.Red500,
  SKIPPED: ColorsWIP.Yellow500,
};

// In CSS, you can layer multiple backgrounds on top of each other by comma-separating values in
// `background`. However, this only works with gradients, not with primitive color values. To do
// hovered + red without color math (?), just stack the colors as flat gradients.
const flatGradient = (color: string) => `linear-gradient(to left, ${color} 0%, ${color} 100%)`;
const flatGradientStack = (colors: string[]) => colors.map(flatGradient).join(',');

const SuccessColorForProps = ({dimSuccesses}: {dimSuccesses?: boolean}) =>
  dimSuccesses ? '#CFE6DC' : STEP_STATUS_COLORS.SUCCESS;

export const GridColumn = styled.div<{
  disabled?: boolean;
  hovered?: boolean;
  focused?: boolean;
  multiselectFocused?: boolean;
  dimSuccesses?: boolean;
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
    background: ${ColorsWIP.Gray100};
    cursor: default;
    ${TopLabelTiltedInner} {
      background: ${ColorsWIP.Gray50};
      .tilted {
        background: ${ColorsWIP.Gray100};
      }
    }
  }`}

  ${({disabled}) =>
    disabled &&
    `
      ${TopLabelTiltedInner} {
        color: ${ColorsWIP.Gray400}
      }
    `}

  ${({focused}) =>
    focused &&
    `background: ${ColorsWIP.Blue500};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTiltedInner} {
      background: ${ColorsWIP.Gray50};
      color: white;
      .tilted {
        background: ${ColorsWIP.Blue500};
      }
    }
  }`}

  ${({multiselectFocused}) =>
    multiselectFocused &&
    `background: ${ColorsWIP.Blue200};
    ${LeftLabel} {
      color: white;
    }
    ${TopLabelTiltedInner} {
      background: ${ColorsWIP.Gray50};
      color: white;
      .tilted {
        background: ${ColorsWIP.Blue200};
      }
    }
  }`}

  .cell {
    height: 23px;
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
    width: 23px;
    height: 23px;
    display: inline-block;

    &:hover:not(.empty) {
      background: ${ColorsWIP.Blue200};
    }
    &:before {
      content: ' ';
      display: inline-block;
      width: 15px;
      height: 15px;
      margin: 4px;
    }
    &.success {
      &:before {
        background: ${SuccessColorForProps};
      }
    }
    &.success-skipped {
      &:before {
        background: linear-gradient(
          135deg,
          ${SuccessColorForProps} 40%,
          ${STEP_STATUS_COLORS.SKIPPED} 41%
        );
      }
    }
    &.success-failure {
      &:before {
        background: linear-gradient(
          135deg,
          ${SuccessColorForProps} 40%,
          ${STEP_STATUS_COLORS.FAILURE} 41%
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
          ${STEP_STATUS_COLORS.FAILURE} 40%,
          ${SuccessColorForProps} 41%
        );
      }
    }
    &.failure-skipped {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 40%,
          ${STEP_STATUS_COLORS.SKIPPED} 41%
        );
      }
    }
    &.failure-blank {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.FAILURE} 40%,
          rgba(150, 150, 150, 0.3) 41%
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
          ${STEP_STATUS_COLORS.SKIPPED} 40%,
          ${SuccessColorForProps} 41%
        );
      }
    }
    &.skipped-failure {
      &:before {
        background: linear-gradient(
          135deg,
          ${STEP_STATUS_COLORS.SKIPPED} 40%,
          ${STEP_STATUS_COLORS.FAILURE} 41%
        );
      }
    }
    &.missing {
      &:before {
        background: ${ColorsWIP.White};
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
      hovered ? ColorsWIP.Gray100 : 'transparent',
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

const TITLE_HEGIHT = 55;
const ROTATION_DEGREES = 41;

export const TopLabelTilted: React.FC<{label: string}> = ({label}) => {
  const node = React.useRef<HTMLDivElement>(null);
  const [tooltip, showTooltip] = React.useState(false);

  // On mount, measure whether the height of the rotated text is greater than the container.
  // If so, we'll display a tooltip so that the text can be made visible on hover.
  React.useEffect(() => {
    if (node.current) {
      const nodeWidth = node.current.offsetWidth;
      const rotatedHeight = Math.sin(ROTATION_DEGREES * (Math.PI / 180)) * nodeWidth;
      if (rotatedHeight > TITLE_HEGIHT) {
        showTooltip(true);
      }
    }
  }, []);

  const content = (
    <TopLabelTiltedInner>
      <div className="tilted" ref={node}>
        {label}
      </div>
    </TopLabelTiltedInner>
  );

  return tooltip ? (
    <Tooltip2 placement="bottom" content={label}>
      {content}
    </Tooltip2>
  ) : (
    content
  );
};

const TopLabelTiltedInner = styled.div`
  position: relative;
  height: ${TITLE_HEGIHT}px;
  padding: 4px;
  padding-bottom: 0;
  min-width: 15px;
  margin-bottom: 15px;
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
  border-right: 1px solid ${ColorsWIP.Gray200};
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
  background: ${ColorsWIP.Gray50};
  flex: 1;
  scrollbar-color: ${ColorsWIP.Gray500} ${ColorsWIP.Gray100};
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
    border: 2px solid ${ColorsWIP.Gray100};
    background-color: ${ColorsWIP.Gray500};
  }
  &::-webkit-scrollbar-track {
    background-color: ${ColorsWIP.Gray100};
  }
`;
