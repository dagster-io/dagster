import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';

import {SearchDialog} from './SearchDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SearchDialog',
  component: SearchDialog,
} as Meta;

const Template: Story = (props) => (
  <StorybookProvider>
    <SearchDialog searchPlaceholder="" {...props} />
  </StorybookProvider>
);

export const Simple = Template.bind({});
