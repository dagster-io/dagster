import {MouseEvent, useRef} from 'react';
import {useHistory} from 'react-router-dom';

import {RunActionsCell} from './RunActionsCell';
import {RunDialog} from './RunDialogs';
import {RunIDCell} from './RunIDCell';
import {RunLaunchCell} from './RunLaunchCell';
import {RunStatusCell} from './RunStatusCell';
import {RunTimingCell} from './RunTimingCell';
import styles from './css/RunRow.module.css';
import {TickIdentifier} from './getLaunchDetails';
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

type RunRowProps = {
  entry: MappedRunsFeedEntry;
  onOpenTickDetails: (tick: TickIdentifier, triggerElement: HTMLElement) => void;
  onOpenRunDialog: (dialog: RunDialog, triggerElement: HTMLElement) => void;
};

export const RunRow = ({entry, onOpenTickDetails, onOpenRunDialog}: RunRowProps) => {
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
      <RunLaunchCell entry={entry} onOpenTickDetails={onOpenTickDetails} />
      <RunStatusCell entry={entry} />
      <div className={styles.divider} />
      <RunTimingCell entry={entry} />
      <div className={styles.divider} />
      <RunIDCell entry={entry} />
      <div className={styles.divider} />
      {entry.__typename === 'Run' && (
        <RunActionsCell run={entry} onOpenRunDialog={onOpenRunDialog} />
      )}
    </div>
  );
};
