import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RepoDetails, RepoSelector} from 'src/nav/RepoSelector';
import {Box} from 'src/ui/Box';
import {buildRepoAddress} from 'src/workspace/buildRepoAddress';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RepoSelector',
  component: RepoSelector,
} as Meta;

// const PIPELINES = new Array(12)
//   .fill(null)
//   .map(() => faker.random.words(2).toLowerCase().replace(' ', '-'));

// const REPO_ONE = `${faker.random.word()}@${faker.random.words(2)}`.toLowerCase().replace(' ', '-');
// const REPO_TWO = `${faker.random.word()}@${faker.random.words(2)}`.toLowerCase().replace(' ', '-');

const OPTIONS = [
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(4).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(6).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.words(5).toLowerCase().replace(/ /g, '-'),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
  },
  {
    repoAddress: buildRepoAddress(
      faker.random.word().toLowerCase(),
      faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    ),
    host: faker.random.word().toLowerCase(),
    port: faker.random.number(9999).toString(),
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
    <Box background={Colors.DARK_GRAY3} padding={16}>
      <RepoSelector options={OPTIONS} onToggle={onToggle} selected={selected} />
    </Box>
  );
};
