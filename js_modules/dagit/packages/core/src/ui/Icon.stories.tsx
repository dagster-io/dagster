import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconWIP as Icon} from './Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Icon',
  component: Icon,
} as Meta;

export const Size16 = () => {
  return (
    <Group direction="row" spacing={2}>
      <Icon name="account_tree" />
      <Icon name="alternate_email" />
      <Icon name="arrow_drop_down" />
      <Icon name="assignment" />
      <Icon name="assignment_turned_in" />
      <Icon name="cached" />
      <Icon name="close" />
      <Icon name="done" />
      <Icon name="error" />
      <Icon name="expand_more" />
      <Icon name="filter_alt" />
      <Icon name="folder" />
      <Icon name="folder_open" />
      <Icon name="history" />
      <Icon name="search" />
      <Icon name="sensors" />
      <Icon name="settings" />
      <Icon name="source" />
      <Icon name="star" />
      <Icon name="toggle_off" />
      <Icon name="toggle_on" />
      <Icon name="warning" />
      <Icon name="workspaces" />
    </Group>
  );
};

export const Size24 = () => {
  return (
    <Group direction="row" spacing={2}>
      <Icon name="account_tree" size={24} />
      <Icon name="alternate_email" size={24} />
      <Icon name="arrow_drop_down" size={24} />
      <Icon name="assignment" size={24} />
      <Icon name="assignment_turned_in" size={24} />
      <Icon name="cached" size={24} />
      <Icon name="close" size={24} />
      <Icon name="done" size={24} />
      <Icon name="error" size={24} />
      <Icon name="expand_more" size={24} />
      <Icon name="filter_alt" size={24} />
      <Icon name="folder" size={24} />
      <Icon name="folder_open" size={24} />
      <Icon name="history" size={24} />
      <Icon name="search" size={24} />
      <Icon name="sensors" size={24} />
      <Icon name="settings" size={24} />
      <Icon name="source" size={24} />
      <Icon name="star" size={24} />
      <Icon name="toggle_off" size={24} />
      <Icon name="toggle_on" size={24} />
      <Icon name="warning" size={24} />
      <Icon name="workspaces" size={24} />
    </Group>
  );
};

export const IconColors = () => {
  return (
    <Group direction="row" spacing={2}>
      <Icon name="account_tree" color={ColorsWIP.Dark} />
      <Icon name="alternate_email" color={ColorsWIP.Gray900} />
      <Icon name="arrow_drop_down" color={ColorsWIP.Gray800} />
      <Icon name="assignment" color={ColorsWIP.Gray700} />
      <Icon name="assignment_turned_in" color={ColorsWIP.Gray600} />
      <Icon name="cached" color={ColorsWIP.Gray500} />
      <Icon name="close" color={ColorsWIP.Gray400} />
      <Icon name="done" color={ColorsWIP.Gray300} />
      <Icon name="error" color={ColorsWIP.Gray200} />
      <Icon name="expand_more" color={ColorsWIP.Gray100} />
      <Icon name="filter_alt" color={ColorsWIP.Gray50} />
      <Icon name="folder" color={ColorsWIP.Blue1} />
      <Icon name="folder_open" color={ColorsWIP.Blue2} />
      <Icon name="history" color={ColorsWIP.Blue3} />
      <Icon name="search" color={ColorsWIP.Blue4} />
      <Icon name="sensors" color={ColorsWIP.Red1} />
      <Icon name="settings" color={ColorsWIP.Red2} />
      <Icon name="source" color={ColorsWIP.Red3} />
      <Icon name="star" color={ColorsWIP.Red4} />
      <Icon name="toggle_off" color={ColorsWIP.Yellow1} />
      <Icon name="toggle_on" color={ColorsWIP.Yellow2} />
      <Icon name="warning" color={ColorsWIP.Yellow3} />
      <Icon name="workspaces" color={ColorsWIP.Yellow4} />
    </Group>
  );
};
