import {Checkbox} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ChangeEvent, MouseEvent, useRef} from 'react';
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
import {SelectionToggle} from '../../hooks/useSelectionReducer';
import {shortenId} from '../../util/shortenId';

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
  checked?: boolean;
  /** Shows a selection checkbox when set. */
  onToggleChecked?: (values: SelectionToggle) => void;
};

export const RunRow = ({
  entry,
  onOpenTickDetails,
  onOpenRunDialog,
  checked = false,
  onToggleChecked,
}: RunRowProps) => {
  const history = useHistory();
  const openInNewTab = useOpenInNewTab();
  const rowRef = useRef<HTMLDivElement>(null);

  const isSelectable = onToggleChecked !== undefined;

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

  const handleCheckboxChange = (event: ChangeEvent<HTMLInputElement>) => {
    const shiftKey =
      event.nativeEvent instanceof globalThis.MouseEvent &&
      event.nativeEvent.getModifierState('Shift');
    onToggleChecked?.({checked: event.target.checked, shiftKey});
  };

  return (
    <div
      ref={rowRef}
      className={clsx(styles.row, isSelectable && styles.selectableRow)}
      onClick={handleRowClick}
      onAuxClick={handleRowClick}
    >
      {isSelectable && (
        <Checkbox
          size="small"
          checked={checked}
          onChange={handleCheckboxChange}
          aria-label={`Select run ${shortenId(entry.id)}`}
        />
      )}
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
