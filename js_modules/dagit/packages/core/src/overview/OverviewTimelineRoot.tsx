import {Page, PageHeader, Heading, Box, TextInput, Button, ButtonGroup} from '@dagster-io/ui';
import * as React from 'react';

import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {QueryfulRunTimeline} from '../runs/QueryfulRunTimeline';
import {useHourWindow, HourWindow} from '../runs/useHourWindow';
import {makeJobKey} from '../runs/useRunsForTimeline';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {OverviewTabs} from './OverviewTabs';

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;
const POLL_INTERVAL = 60 * 1000;

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

export const OverviewTimelineRoot = () => {
  useTrackPageView();
  useDocumentTitle('Runs');

  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);

  const [searchValue, setSearchValue] = React.useState('');
  const [hourWindow, setHourWindow] = useHourWindow('12');
  const [now, setNow] = React.useState(() => Date.now());
  const [offsetMsec, setOffsetMsec] = React.useState(() => 0);

  React.useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => {
      setNow(Date.now());
    }, POLL_INTERVAL);

    return () => {
      clearInterval(timer);
    };
  }, [hourWindow]);

  const onPageEarlier = React.useCallback(() => {
    setOffsetMsec((current) => current - hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageLater = React.useCallback(() => {
    setOffsetMsec((current) => current + hourWindowToOffset(hourWindow));
  }, [hourWindow]);

  const onPageNow = React.useCallback(() => {
    setOffsetMsec(0);
  }, []);

  const range: [number, number] = React.useMemo(
    () => [
      now - Number(hourWindow) * ONE_HOUR + offsetMsec,
      now + LOOKAHEAD_HOURS * ONE_HOUR + offsetMsec,
    ],
    [hourWindow, now, offsetMsec],
  );

  const visibleJobKeys = React.useMemo(() => {
    const searchLower = searchValue.toLocaleLowerCase().trim();
    const flat = visibleRepos.flatMap((repo) => {
      const repoAddress = buildRepoAddress(repo.repository.name, repo.repositoryLocation.name);
      return repo.repository.pipelines
        .filter(({name}) => name.toLocaleLowerCase().includes(searchLower))
        .map((job) => makeJobKey(repoAddress, job.name));
    });
    return new Set(flat);
  }, [visibleRepos, searchValue]);

  return (
    <Page>
      <PageHeader title={<Heading>Overview</Heading>} tabs={<OverviewTabs tab="timeline" />} />
      <Box
        padding={{horizontal: 24, vertical: 16}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}>
          {allRepos.length > 1 && <RepoFilterButton />}
          <TextInput
            icon="search"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Filter by job name…"
            style={{width: '200px'}}
          />
        </Box>
        <Box flex={{direction: 'row', gap: 16, alignItems: 'center'}}>
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
      </Box>
      <QueryfulRunTimeline range={range} visibleJobKeys={visibleJobKeys} />
    </Page>
  );
};
