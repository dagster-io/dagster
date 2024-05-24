import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const BOX_SIZE = 32;

const STEP_STATUS_COLORS = {
  SUCCESS: Colors.accentGreen(),
  SUCCESS_SKIPPED: Colors.accentGreenHover(),
  FAILURE: Colors.accentRed(),
  FAILURE_SKIPPED: Colors.accentRedHover(),
  SKIPPED: Colors.accentYellow(),
  IN_PROGRESS: Colors.accentBlue(),
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
      background: ${Colors.backgroundDefaultHover()};
      cursor: default;
      ${TopLabelTiltedInner} {
        background: ${Colors.backgroundDefaultHover()};
        .tilted {
          background: ${Colors.backgroundLight()};
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
        color: ${Colors.textLight()}
      }
    `}

  ${({focused}) =>
    focused &&
    `background: ${Colors.accentBlue()};
    ${LeftLabel} {
      color: ${Colors.accentReversed()};
    }
    ${TopLabelTiltedInner} {
      background: ${Colors.accentPrimary()};
      color: ${Colors.accentReversed()};
      .tilted {
        background: ${Colors.accentBlue()};
      }
    }
  }`}

  ${({multiselectFocused}) =>
    multiselectFocused &&
    `background: ${Colors.accentBlueHover()};
    ${LeftLabel} {
      color: ${Colors.accentReversed()};
    }
    ${TopLabelTiltedInner} {
      background: ${Colors.accentPrimary()};
      color: ${Colors.accentReversed()};
      .tilted {
        background: ${Colors.accentBlueHover()};
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
      box-shadow: ${Colors.accentBlue()} 0 0 0 3px;
    }
    &:before {
      content: ' ';
      background: ${Colors.accentGray()};
      border-radius: 10px;
      display: inline-block;
      width: 20px;
      height: 20px;
    }
    &.loading {
      &:before {
        background: radial-gradient(
          ${Colors.backgroundGray()} 0%,
          ${Colors.backgroundGray()} 45%,
          ${Colors.backgroundGrayHover()} 60%
        );
      }
    }
    &.success {
      &:before {
        background: ${STEP_STATUS_COLORS.SUCCESS};
      }
    }
    &.failure {
      &:before {
        background: ${STEP_STATUS_COLORS.FAILURE};
      }
    }
    &.success-missing {
      &:before {
        background: ${STEP_STATUS_COLORS.SUCCESS_SKIPPED};
      }
    }
    &.failure-missing {
      &:before {
        background: ${STEP_STATUS_COLORS.FAILURE_SKIPPED};
      }
    }
    &.failure-blank {
      &:before {
        background: ${STEP_STATUS_COLORS.FAILURE_SKIPPED};
      }
    }
    &.skipped {
      &:before {
        background: ${STEP_STATUS_COLORS.SKIPPED};
      }
    }
    &.started,
    &.starting,
    &.canceling {
      &:before {
        background: ${STEP_STATUS_COLORS.IN_PROGRESS};
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
  background: ${({hovered}) =>
    flatGradientStack([hovered ? Colors.backgroundLight() : 'transparent'])};
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

export const TopLabelTilted = ({label, $height}: {label: string; $height: number}) => {
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

export const GRID_FLOATING_CONTAINER_WIDTH = 330;

export const GridFloatingContainer = styled.div<{floating: boolean}>`
  display: flex;
  border-right: 1px solid ${Colors.borderDefault()};
  padding-bottom: 16px;
  width: ${GRID_FLOATING_CONTAINER_WIDTH}px;
  z-index: 1;
  ${({floating}) => (floating ? 'box-shadow: 1px 0 4px rgba(0, 0, 0, 0.15)' : '')};
`;
