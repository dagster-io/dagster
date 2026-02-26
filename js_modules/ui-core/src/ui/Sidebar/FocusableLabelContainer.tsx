import {Colors, MiddleTruncate, UnstyledButton} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

export const FocusableLabelContainer = ({
  isSelected,
  isLastSelected,
  icon,
  text,
}: {
  isSelected: boolean;
  isLastSelected: boolean;
  icon: React.ReactNode;
  text: string;
}) => {
  const ref = React.useRef<HTMLButtonElement | null>(null);
  React.useLayoutEffect(() => {
    // When we click on a node in the graph it also changes "isSelected" in the sidebar.
    // We want to check if the focus is currently in the graph and if it is lets keep it there
    // Otherwise it means the click happened in the sidebar in which case we should move focus to the element
    // in the sidebar
    if (ref.current && isLastSelected && !isElementInsideSVGViewport(document.activeElement)) {
      ref.current.focus();
    }
  }, [isLastSelected]);

  return (
    <GrayOnHoverBox
      ref={ref}
      style={{
        gridTemplateColumns: icon ? 'auto minmax(0, 1fr)' : 'minmax(0, 1fr)',
        gridTemplateRows: 'minmax(0, 1fr)',
        ...(isSelected ? {background: Colors.backgroundBlue()} : {}),
      }}
    >
      {icon}
      <MiddleTruncate text={text} />
    </GrayOnHoverBox>
  );
};

export const GrayOnHoverBox = styled(UnstyledButton)`
  border-radius: 8px;
  user-select: none;
  width: 100%;
  display: grid;
  flex-direction: row;
  height: 32px;
  align-items: center;
  padding: 5px 8px;
  justify-content: space-between;
  gap: 6px;
  flex-grow: 1;
  flex-shrink: 1;
  transition: background 100ms linear;
`;

function isElementInsideSVGViewport(element: Element | null) {
  return !!element?.closest('[data-svg-viewport]');
}
