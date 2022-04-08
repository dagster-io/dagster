import {Box, Colors} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RepoAddress} from '../workspace/types';

import {RepoSelector, RepoSelectorOption} from './RepoSelector';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RepoSelector',
  component: RepoSelector,
} as Meta;
const OPTIONS: RepoSelectorOption[] = [
  {
    repositoryLocation: {
      name: faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(4).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(5).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(6).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(2).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.word().toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(5).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.words(2).toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
  {
    repositoryLocation: {
      name: faker.random.words(1).toLowerCase().replace(/ /g, '-'),
    },
    repository: {
      name: faker.random.words(2).toLowerCase(),
      displayMetadata: [
        {key: 'host', value: faker.random.word().toLowerCase()},
        {key: 'port', value: faker.random.number(9999).toString()},
      ],
    },
  },
];
export const ManyRepos = () => {
  const [selected, setSelected] = React.useState<RepoSelectorOption[]>([]);

  const onToggle = React.useCallback(
    (addresses: RepoAddress[]) => {
      addresses.forEach((address) => {
        const option = OPTIONS.find(
          (r) =>
            r.repository.name === address.name && r.repositoryLocation.name === address.location,
        );
        if (!option) {
          return;
        }
        if (selected.includes(option)) {
          setSelected(selected.filter((o) => o !== option));
        } else {
          setSelected([...selected, option]);
        }
      });
    },
    [selected],
  );

  return (
    <Box background={Colors.Gray800} padding={16}>
      <RepoSelector options={OPTIONS} onBrowse={() => {}} onToggle={onToggle} selected={selected} />
    </Box>
  );
};
