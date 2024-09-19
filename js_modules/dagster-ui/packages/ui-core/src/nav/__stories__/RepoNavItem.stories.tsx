import {Box} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';
import faker from 'faker';
import {useCallback, useState} from 'react';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {RepoAddress} from '../../workspace/types';
import {RepoNavItem} from '../RepoNavItem';
import {RepoSelectorOption} from '../RepoSelector';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RepoNavItem',
  component: RepoNavItem,
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
  const [selected, setSelected] = useState<RepoSelectorOption[]>([]);

  const onToggle = useCallback(
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
    <StorybookProvider>
      <Box flex={{direction: 'column', justifyContent: 'center'}} style={{height: '500px'}}>
        <div style={{width: '234px'}}>
          <RepoNavItem allRepos={OPTIONS} selected={selected} onToggle={onToggle} />
        </div>
      </Box>
    </StorybookProvider>
  );
};

const ONE_REPO = [OPTIONS[0]!];

export const OneRepo = () => {
  const [selected, setSelected] = useState<RepoSelectorOption[]>(ONE_REPO);

  const onToggle = useCallback(
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
    <StorybookProvider>
      <Box flex={{direction: 'column', justifyContent: 'center'}} style={{height: '500px'}}>
        <div style={{width: '234px'}}>
          <RepoNavItem allRepos={ONE_REPO} selected={selected} onToggle={onToggle} />
        </div>
      </Box>
    </StorybookProvider>
  );
};
