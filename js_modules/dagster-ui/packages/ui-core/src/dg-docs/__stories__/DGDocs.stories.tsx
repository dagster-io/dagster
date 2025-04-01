import {Meta} from '@storybook/react';

import {DGDocs} from '../DGDocs';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'dg docs/Page',
  component: DGDocs,
} as Meta;

export const Default = () => {
  return <DGDocs />;
};
