import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ApolloTestProvider} from '../testing/ApolloTestProvider';

import {SearchDialog} from './SearchDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SearchDialog',
  component: SearchDialog,
} as Meta;

const Template: Story = (props) => (
  <ApolloTestProvider>
    <SearchDialog theme="light" searchPlaceholder="" {...props} />
  </ApolloTestProvider>
);

export const Simple = Template.bind({});
