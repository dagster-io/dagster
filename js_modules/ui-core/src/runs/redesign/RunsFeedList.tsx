import {useCallback, useEffect, useRef, useState} from 'react';

import {RunDialog, RunDialogs} from './RunDialogs';
import {RunRow} from './RunRow';
import {RunsFeedSkeleton} from './RunsFeedSkeleton';
import styles from './css/RunsFeedList.module.css';
import {TickIdentifier} from './getLaunchDetails';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {useRestoreFocus} from '../../hooks/useRestoreFocus';
import {TickDetailsDialog} from '../../instigation/TickDetailsDialog';

type RunsFeedListProps = {
  entries: MappedRunsFeedEntry[];
  isLoading: boolean;
};

export const RunsFeedList = ({entries, isLoading}: RunsFeedListProps) => {
  const listRef = useRef<HTMLDivElement>(null);
  const [selectedTick, setSelectedTick] = useState<TickIdentifier | null>(null);
  const [runDialog, setRunDialog] = useState<RunDialog | null>(null);

  // If the dialog's row left the page while it was open, focus the first available link, or the
  // list if there are none.
  const getFallbackFocusTarget = useCallback(
    () => listRef.current?.querySelector<HTMLElement>('a[href]') ?? listRef.current,
    [],
  );
  const {rememberTrigger, restoreFocus} = useRestoreFocus(getFallbackFocusTarget);

  const shouldShowSkeleton = isLoading && entries.length === 0;

  // Restore focus after the dialog unmounts and releases its focus trap.
  useEffect(() => {
    if (!selectedTick && !runDialog) {
      restoreFocus();
    }
  }, [selectedTick, runDialog, restoreFocus]);

  const openTickDetails = (tick: TickIdentifier, triggerElement: HTMLElement) => {
    rememberTrigger(triggerElement);
    setSelectedTick(tick);
  };

  const openRunDialog = (dialog: RunDialog, triggerElement: HTMLElement) => {
    rememberTrigger(triggerElement);
    setRunDialog(dialog);
  };

  return (
    <>
      {/* Keep the live region mounted and outside the busy list so screen readers announce loading. */}
      <span role="status" className={styles.visuallyHidden}>
        {shouldShowSkeleton ? 'Loading runs' : null}
      </span>
      <div ref={listRef} tabIndex={-1} aria-busy={isLoading} className={styles.list}>
        {shouldShowSkeleton ? (
          <RunsFeedSkeleton />
        ) : (
          entries.map((entry) => (
            <RunRow
              key={entry.id}
              entry={entry}
              onOpenTickDetails={openTickDetails}
              onOpenRunDialog={openRunDialog}
            />
          ))
        )}
        {selectedTick && (
          <TickDetailsDialog
            isOpen
            onClose={() => setSelectedTick(null)}
            tickId={selectedTick.tickId}
            instigationSelector={selectedTick.instigationSelector}
          />
        )}
        {runDialog && (
          <RunDialogs
            dialog={runDialog}
            onOpenDialog={setRunDialog}
            onClose={() => setRunDialog(null)}
          />
        )}
      </div>
    </>
  );
};
