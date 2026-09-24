import {useCallback, useEffect, useRef, useState} from 'react';

import {RunRow} from './RunRow';
import {RunsFeedSkeleton} from './RunsFeedSkeleton';
import styles from './css/RunsFeedList.module.css';
import {TickIdentifier} from './getInitiatedBy';
import {MappedRunsFeedEntry} from './mapRunsFeedData';
import {useRestoreFocus} from '../../hooks/useRestoreFocus';
import {TickDetailsDialog} from '../../instigation/TickDetailsDialog';

type Props = {
  entries: MappedRunsFeedEntry[];
  isLoading: boolean;
};

export const RunsFeedList = ({entries, isLoading}: Props) => {
  const listRef = useRef<HTMLDivElement>(null);
  const [selectedTick, setSelectedTick] = useState<TickIdentifier | null>(null);

  // Fall back to the first remaining link, or the list when it is empty.
  const getFallbackFocusTarget = useCallback(
    () => listRef.current?.querySelector<HTMLElement>('a[href]') ?? listRef.current,
    [],
  );
  const {rememberTrigger, restoreFocus} = useRestoreFocus(getFallbackFocusTarget);

  const openTickDetails = (tick: TickIdentifier, triggerElement: HTMLElement) => {
    rememberTrigger(triggerElement);
    setSelectedTick(tick);
  };

  // Restore focus after the dialog unmounts and releases its focus trap.
  useEffect(() => {
    if (selectedTick === null) {
      restoreFocus();
    }
  }, [selectedTick, restoreFocus]);

  const shouldShowSkeleton = isLoading && entries.length === 0;

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
            <RunRow key={entry.id} entry={entry} onOpenTickDetails={openTickDetails} />
          ))
        )}
        {selectedTick !== null && (
          <TickDetailsDialog
            isOpen
            onClose={() => setSelectedTick(null)}
            tickId={selectedTick.tickId}
            instigationSelector={selectedTick.instigationSelector}
          />
        )}
      </div>
    </>
  );
};
