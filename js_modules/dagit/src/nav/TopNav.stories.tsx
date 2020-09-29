import {Tag} from '@blueprintjs/core';
import {Story, Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {TopNav, TopNavProps} from 'src/nav/TopNav';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TopNav',
  component: TopNav,
} as Meta;

const Template: Story<TopNavProps> = (props) => <TopNav {...props} />;

export const WithTabs = Template.bind({});
WithTabs.args = {
  breadcrumbs: [{text: 'Pipelines', icon: 'diagram-tree'}, {text: 'cool_pipeline'}],
  tabs: [
    {text: 'Overview', href: '#'},
    {text: 'Definition', href: '#'},
  ],
};

export const WithoutTabs = Template.bind({});
WithoutTabs.args = {
  breadcrumbs: [{text: 'Pipelines', icon: 'diagram-tree'}, {text: 'cool_pipeline'}],
};

export const WithTag = Template.bind({});
WithTag.args = {
  breadcrumbs: [
    {text: 'Snapshots', icon: 'camera'},
    {
      text: (
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div style={{marginRight: '12px'}}>c513370e7e15df09c9edd297dfa8f3b4</div>
          <Tag minimal intent="warning">
            Historical snapshot
          </Tag>
        </div>
      ),
    },
  ],
};

export const WithTagAndTabs = Template.bind({});
WithTagAndTabs.args = {
  breadcrumbs: [
    {text: 'Snapshots', icon: 'camera'},
    {
      text: (
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div style={{marginRight: '12px'}}>c513370e7e15df09c9edd297dfa8f3b4</div>
          <Tag minimal intent="warning">
            Historical snapshot
          </Tag>
        </div>
      ),
    },
  ],
  tabs: [
    {text: 'Overview', href: '#'},
    {text: 'Definition', href: '#'},
  ],
};
