import {Colors, Icon, Tooltip} from '@dagster-io/ui-components';
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

const HandleContainer = styled.div<{
  $placement: 'header' | 'edge';
}>`
  ${(p) => placementStyles[p.$placement]}
  display: inline-flex;
  align-items: center;
  gap: 2px;
  z-index: 2;
`;

const ControlButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: ${Colors.textLight()};

  &:hover {
    background: ${Colors.backgroundLightHover()};
    color: ${Colors.textDefault()};
  }
`;

const HandleButton = styled(ControlButton)<{
  $isDragging: boolean;
  $isManuallyPositioned: boolean;
}>`
  color: ${(p) =>
    p.$isDragging || p.$isManuallyPositioned ? Colors.accentBlue() : Colors.textLight()};
  cursor: ${(p) => (p.$isDragging ? 'grabbing' : 'grab')};

  &:hover {
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

  return (
    <HandleContainer $placement={placement}>
      <Tooltip content="Drag to reposition">
        <HandleButton
          type="button"
          aria-label="Drag to reposition"
          $isDragging={isDragging}
          $isManuallyPositioned={isManuallyPositioned}
          onMouseDown={(e) => {
            e.stopPropagation();
            onDragStart(e);
          }}
          onClick={(e) => {
            e.stopPropagation();
          }}
        />
      </Tooltip>
      {isResettable ? (
        <Tooltip content="Reset to auto-layout">
          <ControlButton
            type="button"
            aria-label="Reset to auto-layout"
            onMouseDown={(e) => {
              e.stopPropagation();
            }}
            onClick={(e) => {
              e.stopPropagation();
              onReset();
            }}
          >
            <Icon name="refresh" />
          </ControlButton>
        </Tooltip>
      ) : null}
    </HandleContainer>
  );
};
