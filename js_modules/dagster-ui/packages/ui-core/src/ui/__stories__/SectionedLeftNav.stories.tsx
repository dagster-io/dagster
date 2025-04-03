import {Meta} from '@storybook/react';

import {LEFT_NAV_WIDTH} from '../../nav/LeftNav';
import {
  abcLocationOption,
  fooBarOption,
  loremIpsumOption,
} from '../../nav/__fixtures__/LeftNavRepositorySection.fixtures';
import {SectionedLeftNav} from '../SectionedLeftNav';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SectionedLeftNav',
  component: SectionedLeftNav,
} as Meta;

export const Default = () => {
  return (
    <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: LEFT_NAV_WIDTH}}>
      <SectionedLeftNav visibleRepos={[loremIpsumOption, fooBarOption, abcLocationOption]} />
    </div>
  );
};

export const SingleRepo = () => {
  return (
    <div style={{position: 'absolute', left: 0, top: 0, height: '100%', width: LEFT_NAV_WIDTH}}>
      <SectionedLeftNav visibleRepos={[loremIpsumOption]} />
    </div>
  );
};
