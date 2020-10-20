import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {SearchDialog} from 'src/search/SearchDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SearchDialog',
  component: SearchDialog,
} as Meta;

const Template: Story<{}> = (props) => <SearchDialog {...props} />;

export const Simple = Template.bind({});
