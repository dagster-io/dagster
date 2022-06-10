import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {LEFT_NAV_WIDTH} from '../nav/LeftNav';
import {StorybookProvider} from '../testing/StorybookProvider';
import {defaultMocks, hyphenatedName} from '../testing/defaultMocks';

import {SectionedLeftNav} from './SectionedLeftNav';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SectionedLeftNav',
  component: SectionedLeftNav,
} as Meta;

const names = [hyphenatedName(4), hyphenatedName(4), hyphenatedName(4), hyphenatedName(4)];
let repoIndex = 0;
let nameIndex = 0;

export const Default = () => {
  const mocks = {
    Pipeline: () => ({
      name: () => names[nameIndex++ % 4],
      modes: () => [...new Array(1)],
      isAssetJob: () => false,
    }),
    Schedule: () => ({
      id: hyphenatedName,
      name: hyphenatedName,
      pipelineName: () => names[0],
      results: () => [...new Array(1)],
    }),
    Sensor: () => ({
      id: hyphenatedName,
      name: hyphenatedName,
      targets: () => [
        {
          pipelineName: names[1],
          mode: 'mistmatching_mode',
        },
      ],
      results: () => [...new Array(1)],
    }),
    Repository: () => ({
      ...defaultMocks.Repository(),
      name: () => (repoIndex++ % 2 === 0 ? 'default' : hyphenatedName(4)),
      sensors: () => (repoIndex === 1 ? [...new Array(2)] : []),
      schedules: () => (repoIndex === 1 ? [...new Array(2)] : []),
    }),
    RepositoryLocation: () => ({
      ...defaultMocks.RepositoryLocation(),
      name: () => hyphenatedName(6),
    }),
    Workspace: () => ({
      ...defaultMocks.Workspace(),
      locationEntries: () => [...new Array(2)],
    }),
  };

  return (
    <StorybookProvider apolloProps={{mocks}}>
      <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: LEFT_NAV_WIDTH}}>
        <SectionedLeftNav />
      </div>
    </StorybookProvider>
  );
};

export const SingleRepo = () => {
  const mocks = {
    Repository: () => ({
      ...defaultMocks.Repository(),
      pipelines: () => [...new Array(15)],
    }),
    RepositoryLocation: () => ({
      environmentPath: () => 'what then',
      id: () => 'my_location',
      name: () => 'my_location',
      repositories: () => [...new Array(1)],
    }),
    Workspace: () => ({
      ...defaultMocks.Workspace(),
      locationEntries: () => [...new Array(1)],
    }),
  };

  return (
    <StorybookProvider apolloProps={{mocks}}>
      <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: LEFT_NAV_WIDTH}}>
        <SectionedLeftNav />
      </div>
    </StorybookProvider>
  );
};
