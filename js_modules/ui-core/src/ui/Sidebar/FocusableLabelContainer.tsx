import {Colors, MiddleTruncate, UnstyledButton} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './css/FocusableLabelContainer.module.css';

export const GRAY_ON_HOVER_BOX_CLASS = styles.grayOnHoverBox;

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
    <UnstyledButton
      ref={ref}
      className={`${styles.grayOnHoverBox} GrayOnHoverBox`}
      style={{
        gridTemplateColumns: icon ? 'auto minmax(0, 1fr)' : 'minmax(0, 1fr)',
        gridTemplateRows: 'minmax(0, 1fr)',
        ...(isSelected ? {background: Colors.backgroundBlue()} : {}),
      }}
    >
      {icon}
      <MiddleTruncate text={text} />
    </UnstyledButton>
  );
};

function isElementInsideSVGViewport(element: Element | null) {
  return !!element?.closest('[data-svg-viewport]');
}
