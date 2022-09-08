import {Page, PageHeader, Heading, Box, TextInput, ButtonGroup} from '@dagster-io/ui';
import * as React from 'react';

import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {QueryfulRunTimeline} from './QueryfulRunTimeline';
import {RunListTabs} from './RunListTabs';
import {HourWindow, useHourWindow} from './useHourWindow';
import {makeJobKey} from './useRunsForTimeline';

const LOOKAHEAD_HOURS = 1;
const ONE_HOUR = 60 * 60 * 1000;
const POLL_INTERVAL = 60 * 1000;

export const RunTimelineRoot = () => {
  useTrackPageView();
  useDocumentTitle('Runs');

  const {allRepos, visibleRepos} = React.useContext(WorkspaceContext);

  const [searchValue, setSearchValue] = React.useState('');
  const [hourWindow, setHourWindow] = useHourWindow('12');
  const [now, setNow] = React.useState(() => Date.now());

  React.useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => {
      setNow(Date.now());
    }, POLL_INTERVAL);

    return () => {
      clearInterval(timer);
    };
  }, [hourWindow]);

  const range: [number, number] = React.useMemo(
    () => [now - Number(hourWindow) * ONE_HOUR, now + LOOKAHEAD_HOURS * ONE_HOUR],
    [hourWindow, now],
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
      <PageHeader title={<Heading>Runs</Heading>} tabs={<RunListTabs />} />
      <Box
        padding={{horizontal: 24, top: 16}}
        flex={{alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12, grow: 0}}>
          {allRepos.length > 1 && <RepoFilterButton />}
          <TextInput
            icon="search"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Filter by job name…"
            style={{width: '340px'}}
          />
        </Box>
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
      </Box>
      <QueryfulRunTimeline range={range} visibleJobKeys={visibleJobKeys} />
    </Page>
  );
};
