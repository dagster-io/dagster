import {Colors, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';
import styled, {css} from 'styled-components';

type ManualPositionHandleProps = {
  isDragging?: boolean;
  isManuallyPositioned?: boolean;
  onDragStart: (e: React.MouseEvent<HTMLButtonElement>) => void;
  onReset?: () => void;
  placement?: 'header' | 'edge';
};

const placementStyles = {
  header: css`
    position: relative;
  `,
  edge: css`
    position: absolute;
    top: 50%;
    right: 4px;
    transform: translateY(-50%);
    z-index: 2;
  `,
};

const HandleButton = styled.button<{
  $isDragging: boolean;
  $isManuallyPositioned: boolean;
  $placement: 'header' | 'edge';
}>`
  ${(p) => placementStyles[p.$placement]}
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: ${(p) =>
    p.$isDragging || p.$isManuallyPositioned ? Colors.accentBlue() : Colors.textLight()};
  cursor: ${(p) => (p.$isDragging ? 'grabbing' : 'grab')};

  &:hover {
    background: ${Colors.backgroundLightHover()};
    color: ${(p) => (p.$isManuallyPositioned ? Colors.accentBlue() : Colors.textDefault())};
  }

  &::before {
    content: '';
    width: 2px;
    height: 2px;
    border-radius: 999px;
    background: currentColor;
    box-shadow:
      0 6px 0 currentColor,
      0 -6px 0 currentColor,
      6px 0 0 currentColor,
      6px 6px 0 currentColor,
      6px -6px 0 currentColor;
  }
`;

export const ManualPositionHandle = ({
  isDragging = false,
  isManuallyPositioned = false,
  onDragStart,
  onReset,
  placement = 'header',
}: ManualPositionHandleProps) => {
  const isResettable = isManuallyPositioned && !!onReset;
  const tooltipContent = isResettable
    ? 'Drag to reposition. Double-click to reset position.'
    : 'Drag to reposition';

  return (
    <Tooltip content={tooltipContent}>
      <HandleButton
        type="button"
        aria-label={isResettable ? 'Reset position' : 'Drag to reposition'}
        $isDragging={isDragging}
        $isManuallyPositioned={isManuallyPositioned}
        $placement={placement}
        onMouseDown={(e) => {
          e.stopPropagation();
          onDragStart(e);
        }}
        onClick={(e) => {
          e.stopPropagation();
        }}
        onDoubleClick={(e) => {
          e.stopPropagation();
          if (isResettable) {
            onReset();
          }
        }}
      />
    </Tooltip>
  );
};
