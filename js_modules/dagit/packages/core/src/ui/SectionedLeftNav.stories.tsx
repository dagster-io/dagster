import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {LEFT_NAV_WIDTH} from '../nav/LeftNav';
import {StorybookProvider} from '../testing/StorybookProvider';
import {defaultMocks} from '../testing/defaultMocks';

import {SectionedLeftNav} from './SectionedLeftNav';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SectionedLeftNav',
  component: SectionedLeftNav,
} as Meta;

const mocks = {
  Repository: () => ({
    ...defaultMocks.Repository(),
    pipelines: () => [...new Array(15)],
  }),
  Workspace: () => ({
    ...defaultMocks.Workspace(),
    locationEntries: () => [...new Array(2)],
  }),
};

export const Default = () => {
  return (
    <StorybookProvider apolloProps={{mocks}}>
      <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: LEFT_NAV_WIDTH}}>
        <SectionedLeftNav />
      </div>
    </StorybookProvider>
  );
};
