import {Box} from '@dagster-io/ui-components';
import {MouseEvent, useRef} from 'react';
import {useHistory} from 'react-router-dom';

import {RunIDCell} from './RunIDCell';
import {RunInitiatedByCell} from './RunInitiatedByCell';
import {RunStatusCell} from './RunStatusCell';
import {RunTargetsCell} from './RunTargetsCell';
import styles from './css/RunRow.module.css';
import {TickIdentifier} from './getInitiatedBy';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {isNewTabClick, useOpenInNewTab} from '../../hooks/useOpenInNewTab';

const PRIMARY_MOUSE_BUTTON = 0;
const AUXILIARY_MOUSE_BUTTON = 1;
const INTERACTIVE_ELEMENT_SELECTOR =
  'a, button, input, select, textarea, label, [role="button"], [role="link"], [contenteditable]';

// Only navigate for non-interactive content inside the row; portaled content can bubble through React.
const isRowNavigationTarget = (row: HTMLElement | null, target: EventTarget | null) =>
  row !== null &&
  target instanceof Element &&
  row.contains(target) &&
  target.closest(INTERACTIVE_ELEMENT_SELECTOR) === null;

type Props = {
  entry: MappedRunsFeedEntry;
  onOpenTickDetails: (tick: TickIdentifier, triggerElement: HTMLElement) => void;
};

export const RunRow = ({entry, onOpenTickDetails}: Props) => {
  const history = useHistory();
  const openInNewTab = useOpenInNewTab();
  const rowRef = useRef<HTMLDivElement>(null);

  const handleRowClick = (event: MouseEvent<HTMLDivElement>) => {
    if (
      !isRowNavigationTarget(rowRef.current, event.target) ||
      document.getSelection()?.toString()
    ) {
      return;
    }

    if (event.button === AUXILIARY_MOUSE_BUTTON) {
      // The middle button would otherwise start autoscroll alongside the new tab.
      event.preventDefault();
      openInNewTab(entry.href);
      return;
    }

    if (event.button !== PRIMARY_MOUSE_BUTTON || event.altKey) {
      return;
    }

    if (isNewTabClick(event) || event.shiftKey) {
      openInNewTab(entry.href);
      return;
    }

    history.push(entry.href);
  };

  return (
    <div ref={rowRef} className={styles.row} onClick={handleRowClick} onAuxClick={handleRowClick}>
      <div className={styles.initiatorAndTargets}>
        <RunInitiatedByCell entry={entry} onOpenTickDetails={onOpenTickDetails} />
        <RunTargetsCell entry={entry} />
      </div>
      <RunStatusCell entry={entry} />
      <Box border="left" padding={{left: 16}}>
        <RunIDCell entry={entry} />
      </Box>
    </div>
  );
};
