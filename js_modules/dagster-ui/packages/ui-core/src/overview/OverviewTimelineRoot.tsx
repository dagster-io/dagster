import {Box, Button, ButtonGroup, ErrorBoundary} from '@dagster-io/ui-components';
import * as React from 'react';
import {useDeferredValue, useMemo} from 'react';

import {GroupTimelineRunsBySelect} from './GroupTimelineRunsBySelect';
import {groupRunsByAutomation} from './groupRunsByAutomation';
import {useGroupTimelineRunsBy} from './useGroupTimelineRunsBy';
import {RefreshState} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {usePrefixedCacheKey} from '../app/usePrefixedCacheKey';
import {useAutomations} from '../automation/useAutomations';
import {filterAutomationSelectionByQuery} from '../automation-selection/AntlrAutomationSelection';
import {AutomationSelectionInput} from '../automation-selection/input/AutomationSelectionInput';
import {Automation} from '../automation-selection/input/useAutomationSelectionAutoCompleteProvider';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryAndLocalStoragePersistedState} from '../hooks/useQueryAndLocalStoragePersistedState';
import {filterJobSelectionByQuery} from '../job-selection/AntlrJobSelection';
import {JobSelectionInput} from '../job-selection/input/JobSelectionInput';
import {RunTimeline} from '../runs/RunTimeline';
import {HourWindow, useHourWindow} from '../runs/useHourWindow';
import {useRunsForTimeline} from '../runs/useRunsForTimeline';

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;
const POLL_INTERVAL = 30 * 1000;

const hourWindowToOffset = (hourWindow: HourWindow) => {
  switch (hourWindow) {
    case '1':
      return ONE_HOUR;
    case '6':
      return 6 * ONE_HOUR;
    case '12':
      return 12 * ONE_HOUR;
    case '24':
      return 24 * ONE_HOUR;
  }
};

type Props = {
  Header: React.ComponentType<{refreshState: RefreshState}>;
  TabButton: React.ComponentType<{selected: 'timeline' | 'assets'}>;
};

export function useTimelineRange({
  maxNowMs,
  hourWindowStorageKey,
  hourWindowDefault = '12',
  lookaheadHours = LOOKAHEAD_HOURS,
}: {
  maxNowMs?: number;
  hourWindowStorageKey?: string;
  hourWindowDefault?: HourWindow;
  lookaheadHours?: number;
}) {
  const [hourWindow, setHourWindow] = useHourWindow(hourWindowDefault, hourWindowStorageKey);
  const [now, setNow] = React.useState(() => maxNowMs || Date.now());
  const [offsetMsec, setOffsetMsec] = React.useState(() => 0);

  const rangeMs: [number, number] = React.useMemo(
    () => [
      now - Number(hourWindow) * ONE_HOUR + offsetMsec,
      now + lookaheadHours * ONE_HOUR + offsetMsec,
    ],
    [hourWindow, now, lookaheadHours, offsetMsec],
  );

  React.useEffect(() => {
    const timer = setInterval(() => {
      setNow(maxNowMs ? Math.min(maxNowMs, Date.now()) : Date.now());
    }, POLL_INTERVAL);

    return () => {
      clearInterval(timer);
    };
  }, [hourWindow, maxNowMs]);

  const onPageEarlier = React.useCallback(() => {
    setOffsetMsec((current) => current - hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageLater = React.useCallback(() => {
    setOffsetMsec((current) => current + hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageNow = React.useCallback(() => {
    setOffsetMsec(0);
  }, []);

  return {rangeMs, hourWindow, setHourWindow, onPageEarlier, onPageLater, onPageNow};
}

export const OverviewTimelineRoot = ({Header}: Props) => {
  useTrackPageView();
  useDocumentTitle('Overview | Timeline');
  const {rangeMs, hourWindow, setHourWindow, onPageEarlier, onPageLater, onPageNow} =
    useTimelineRange({});

  const [groupRunsBy, setGroupRunsBy] = useGroupTimelineRunsBy();

  const {automations: allAutomations} = useAutomations();

  const [jobSelection, setJobSelection] = useQueryAndLocalStoragePersistedState<string>({
    queryKey: 'jobSelection',
    defaults: {jobSelection: ''},
    localStorageKey: usePrefixedCacheKey('jobSelection'),
    isEmptyState: (state) => state === '',
  });
  const [automationSelection, setAutomationSelection] =
    useQueryAndLocalStoragePersistedState<string>({
      queryKey: 'automationSelection',
      defaults: {automationSelection: ''},
      localStorageKey: usePrefixedCacheKey('automationSelection'),
      isEmptyState: (state) => state === '',
    });

  const runsForTimelineRet = useRunsForTimeline({rangeMs});

  // Use deferred value to allow paginating quickly with the UI feeling more responsive.
  const {jobs: jobsUnmapped, loading, refreshState} = useDeferredValue(runsForTimelineRet);

  const automationRows = useMemo(() => {
    const sensors = Object.fromEntries(
      allAutomations
        .filter((automation) => automation.type === 'sensor')
        .map((automation) => [automation.name, automation]),
    );
    const schedules = Object.fromEntries(
      allAutomations
        .filter((automation) => automation.type === 'schedule')
        .map((automation) => [automation.name, automation]),
    );
    return groupRunsByAutomation(jobsUnmapped).map((automation) => ({
      ...automation,
      repo: automation.repoAddress,
      type: automation.type as Automation['type'],
      status:
        automation.type === 'sensor'
          ? (sensors[automation.name]?.status ?? 'running')
          : (schedules[automation.name]?.status ?? 'running'),
      tags:
        automation.type === 'sensor'
          ? (sensors[automation.name]?.tags ?? [])
          : (schedules[automation.name]?.tags ?? []),
    }));
  }, [allAutomations, jobsUnmapped]);

  const jobRows = useMemo(() => {
    return jobsUnmapped.map((job) => ({
      ...job,
      repo: job.repoAddress,
    }));
  }, [jobsUnmapped]);

  const rows = useMemo(() => {
    if (groupRunsBy === 'automation') {
      return Array.from(filterAutomationSelectionByQuery(automationRows, automationSelection));
    }
    return Array.from(filterJobSelectionByQuery(jobRows, jobSelection).all);
  }, [automationSelection, automationRows, groupRunsBy, jobSelection, jobRows]);

  return (
    <>
      <Header refreshState={refreshState} />
      <Box padding={{horizontal: 24, vertical: 12}} flex={{alignItems: 'center', gap: 16}}>
        <GroupTimelineRunsBySelect value={groupRunsBy} onSelect={setGroupRunsBy} />
        <div style={{flex: 1, display: 'flex', alignItems: 'center'}}>
          {groupRunsBy === 'automation' ? (
            <AutomationSelectionInput
              items={automationRows}
              value={automationSelection}
              onChange={(value) => setAutomationSelection(value)}
            />
          ) : (
            <JobSelectionInput items={jobRows} value={jobSelection} onChange={setJobSelection} />
          )}
        </div>
        <ButtonGroup<HourWindow>
          activeItems={new Set([hourWindow])}
          buttons={[
            {id: '1', label: '1hr'},
            {id: '6', label: '6hr'},
            {id: '12', label: '12hr'},
            {id: '24', label: '24hr'},
          ]}
          onClick={(hrWindow: HourWindow) => setHourWindow(hrWindow)}
        />
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Button onClick={onPageEarlier}>&larr;</Button>
          <Button onClick={onPageNow}>Now</Button>
          <Button onClick={onPageLater}>&rarr;</Button>
        </Box>
      </Box>
      <ErrorBoundary region="timeline">
        <RunTimeline loading={loading} rangeMs={rangeMs} rows={rows} />
      </ErrorBoundary>
    </>
  );
};
