import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {RepoDetails, RepoSelector} from './RepoSelector';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RepoSelector',
  component: RepoSelector,
} as Meta;

const OPTIONS = [
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(4).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(6).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    isReloadSupported: true,
    metadata: [
      {key: 'host', value: faker.random.word().toLowerCase()},
      {key: 'port', value: faker.random.number(9999).toString()},
    ],
  },
];

export const ManyRepos = () => {
  const [selected, setSelected] = React.useState<Set<RepoDetails>>(() => new Set());

  const onToggle = React.useCallback(
    (repoDetails: RepoDetails) => {
      const copy = new Set(selected);
      if (selected.has(repoDetails)) {
        copy.delete(repoDetails);
      } else {
        copy.add(repoDetails);
      }
      setSelected(copy);
    },
    [selected],
  );

  return (
    <Box background={ColorsWIP.Gray800} padding={16}>
      <RepoSelector options={OPTIONS} onBrowse={() => {}} onToggle={onToggle} selected={selected} />
    </Box>
  );
};
