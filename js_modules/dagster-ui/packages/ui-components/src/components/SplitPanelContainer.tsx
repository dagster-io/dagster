import {forwardRef, useCallback, useImperativeHandle, useRef, useState} from 'react';
import styled from 'styled-components';

import {Colors} from './Color';

const DIVIDER_THICKNESS = 2;

interface SplitPanelContainerProps {
  axis?: 'horizontal' | 'vertical';
  identifier: string;
  first: React.ReactNode;
  firstInitialPercent: number;
  firstMinSize?: number;
  secondMinSize?: number;
  second: React.ReactNode | null; // Note: pass null to hide / animate away the second panel
}

export type SplitPanelContainerHandle = {
  getSize: () => number;
  changeSize: (value: number) => void;
};

export const SplitPanelContainer = forwardRef<SplitPanelContainerHandle, SplitPanelContainerProps>(
  (props, ref) => {
    const {
      axis = 'horizontal',
      identifier,
      first,
      firstInitialPercent,
      firstMinSize,
      secondMinSize = 0,
      second,
    } = props;

    const [_, setTrigger] = useState(0);
    const [resizing, setResizing] = useState(false);
    const key = `dagster.panel-width.${identifier}`;

    const getSize = useCallback(() => {
      if (!second) {
        return 100;
      }
      const storedSize = window.localStorage.getItem(key);
      const parsed = storedSize === null ? null : parseFloat(storedSize);
      return parsed === null || isNaN(parsed) ? firstInitialPercent : parsed;
    }, [firstInitialPercent, key, second]);

    const onChangeSize = useCallback(
      (newValue: number) => {
        window.localStorage.setItem(key, `${newValue}`);
        setTrigger((current) => (current ? 0 : 1));
      },
      [key],
    );

    useImperativeHandle(ref, () => ({getSize, changeSize: onChangeSize}), [onChangeSize, getSize]);

    const firstSize = getSize();

    const firstPaneStyles: React.CSSProperties = {flexShrink: 0};

    // Note: The divider appears after the first panel, so making the first panel 100% wide
    // hides the divider offscreen. To prevent this, we subtract the divider depth.
    if (axis === 'horizontal') {
      firstPaneStyles.minWidth = firstMinSize;
      firstPaneStyles.width = `calc(${firstSize / 100} * (100% - ${
        DIVIDER_THICKNESS + (second ? secondMinSize : 0)
      }px))`;
    } else {
      firstPaneStyles.minHeight = firstMinSize;
      firstPaneStyles.height = `calc(${firstSize / 100} * (100% - ${
        DIVIDER_THICKNESS + (second ? secondMinSize : 0)
      }px))`;
    }

    return (
      <Container axis={axis} className="split-panel-container" resizing={resizing}>
        <div className="split-panel" style={firstPaneStyles}>
          {first}
        </div>
        <PanelDivider
          axis={axis}
          resizing={resizing}
          secondMinSize={secondMinSize}
          onSetResizing={setResizing}
          onMove={onChangeSize}
        />
        <div className="split-panel" style={{flex: 1}}>
          {second}
        </div>
      </Container>
    );
  },
);

interface IDividerProps {
  axis: 'horizontal' | 'vertical';
  resizing: boolean;
  secondMinSize: number;
  onSetResizing: (resizing: boolean) => void;
  onMove: (vw: number) => void;
}

const PanelDivider = (props: IDividerProps) => {
  const {axis, resizing, secondMinSize, onSetResizing, onMove} = props;
  const ref = useRef<HTMLDivElement>(null);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();

    onSetResizing(true);

    const onMouseMove = (event: MouseEvent) => {
      const parent = ref.current?.closest('.split-panel-container');
      if (!parent) {
        return;
      }
      const parentRect = parent.getBoundingClientRect();

      const firstPanelPercent =
        axis === 'horizontal'
          ? ((event.clientX - parentRect.left) * 100) /
            (parentRect.width - secondMinSize - DIVIDER_THICKNESS)
          : ((event.clientY - parentRect.top) * 100) /
            (parentRect.height - secondMinSize - DIVIDER_THICKNESS);

      onMove(Math.min(100, Math.max(0, firstPanelPercent)));
    };

    const onMouseUp = () => {
      onSetResizing(false);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const hitArea =
    axis === 'horizontal' ? (
      <HorizontalDividerHitArea onMouseDown={onMouseDown} />
    ) : (
      <VerticalDividerHitArea onMouseDown={onMouseDown} />
    );

  return axis === 'horizontal' ? (
    <HorizontalDividerWrapper $resizing={resizing} ref={ref}>
      {hitArea}
    </HorizontalDividerWrapper>
  ) : (
    <VerticalDividerWrapper $resizing={resizing} ref={ref}>
      {hitArea}
    </VerticalDividerWrapper>
  );
};

// Note: -1px margins here let the divider cover the last 1px of the previous box, hiding
// any scrollbar border it might have.

const HorizontalDividerWrapper = styled.div<{$resizing: boolean}>`
  width: ${DIVIDER_THICKNESS}px;
  z-index: 1;
  background: ${(p) => (p.$resizing ? Colors.accentGray() : Colors.keylineDefault())};
  margin-left: -1px;
  overflow: visible;
  position: relative;
`;
const VerticalDividerWrapper = styled.div<{$resizing: boolean}>`
  height: ${DIVIDER_THICKNESS}px;
  z-index: 1;
  background: ${(p) => (p.$resizing ? Colors.accentGray() : Colors.keylineDefault())};
  margin-top: -1px;
  overflow: visible;
  position: relative;
`;

const HorizontalDividerHitArea = styled.div`
  width: 17px;
  height: 100%;
  z-index: 1;
  cursor: ew-resize;
  position: relative;
  left: -8px;
`;
const VerticalDividerHitArea = styled.div`
  height: 17px;
  width: 100%;
  z-index: 1;
  cursor: ns-resize;
  position: relative;
  top: -8px;
`;

const Container = styled.div<{
  axis?: 'horizontal' | 'vertical';
  resizing: boolean;
}>`
  display: flex;
  overflow: hidden;
  flex-direction: ${({axis}) => (axis === 'vertical' ? 'column' : 'row')};
  flex: 1 1;
  width: 100%;
  min-width: 0;
  min-height: 0;

  .split-panel {
    position: relative;
    transition: ${({axis, resizing}) =>
      resizing ? 'none' : axis === 'horizontal' ? 'width' : 'height'}
      200ms ease-out;
    flex-direction: column;
    display: flex;
    min-${({axis}) => (axis === 'vertical' ? 'height' : 'width')}: 0;
    z-index: 0;
  }
`;
