import {Box, TextInput} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';

import {VirtualizedJobTable} from './VirtualizedJobTable';
import {buildRepoAddress} from './buildRepoAddress';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'VirtualizedJobTable',
  component: VirtualizedJobTable,
} as Meta;

const mocks = {
  Pipeline: () => ({
    isJob: () => true,
    description: () => faker.random.words(4),
  }),
};

export const Standard = () => {
  const [searchValue, setSearchValue] = React.useState('');

  const repoAddress = React.useMemo(
    () =>
      buildRepoAddress(
        faker.random.word().toLocaleLowerCase(),
        faker.random.word().toLocaleLowerCase(),
      ),
    [],
  );

  const jobs = React.useMemo(
    () =>
      new Array(3000).fill(null).map(() => ({
        name: faker.random.words(2).replace(' ', '-').toLocaleLowerCase(),
        isJob: true,
      })),
    [],
  );

  const onChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const filtered = React.useMemo(() => {
    const searchLower = searchValue.toLocaleLowerCase();
    return jobs.filter(({name}) => name.includes(searchLower));
  }, [searchValue, jobs]);

  return (
    <StorybookProvider apolloProps={{mocks}}>
      <div style={{position: 'fixed', height: '100%', width: '100%'}}>
        <Box padding={{horizontal: 24, vertical: 12}}>
          <TextInput value={searchValue} onChange={onChange} placeholder="Search for a job…" />
        </Box>
        <VirtualizedJobTable repoAddress={repoAddress} jobs={filtered} />
      </div>
    </StorybookProvider>
  );
};
