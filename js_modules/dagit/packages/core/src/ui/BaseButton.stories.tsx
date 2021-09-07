import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {BaseButton} from './BaseButton';
import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconWIP as Icon} from './Icon';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'BaseButton',
  component: BaseButton,
} as Meta;

export const Default = () => {
  return (
    <Group direction="column" spacing={8}>
      <BaseButton label="Button" />
      <BaseButton label="Button" icon={<Icon name="star" />} />
      <BaseButton label="Button" rightIcon={<Icon name="close" />} />
      <BaseButton
        label="Button"
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      />
      <BaseButton icon={<Icon name="cached" />} />
    </Group>
  );
};

export const Fill = () => {
  return (
    <Group direction="column" spacing={8}>
      <BaseButton
        label="Button"
        fillColor={ColorsWIP.Dark}
        textColor={ColorsWIP.White}
        stroke={false}
      />
      <BaseButton
        label="Button"
        fillColor={ColorsWIP.Blue700}
        textColor={ColorsWIP.White}
        stroke={false}
        icon={<Icon name="star" />}
      />
      <BaseButton
        label="Button"
        fillColor={ColorsWIP.Green700}
        textColor={ColorsWIP.White}
        stroke={false}
        rightIcon={<Icon name="close" />}
      />
      <BaseButton
        label="Button"
        fillColor={ColorsWIP.Red700}
        textColor={ColorsWIP.White}
        stroke={false}
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      />
      <BaseButton
        fillColor={ColorsWIP.Yellow700}
        textColor={ColorsWIP.White}
        stroke={false}
        icon={<Icon name="cached" />}
      />
    </Group>
  );
};

export const Transparent = () => {
  return (
    <Box padding={12} background={ColorsWIP.Gray200}>
      <Group direction="column" spacing={8}>
        <BaseButton textColor={ColorsWIP.Dark} label="Button" fillColor="transparent" />
        <BaseButton
          textColor={ColorsWIP.Dark}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="star" />}
        />
        <BaseButton
          textColor={ColorsWIP.Dark}
          label="Button"
          fillColor="transparent"
          rightIcon={<Icon name="close" />}
        />
        <BaseButton
          textColor={ColorsWIP.Dark}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="source" />}
          rightIcon={<Icon name="expand_more" />}
        />
        <BaseButton
          textColor={ColorsWIP.Dark}
          fillColor="transparent"
          icon={<Icon name="cached" />}
        />
      </Group>
    </Box>
  );
};

export const Disabled = () => {
  return (
    <Group direction="column" spacing={8}>
      <BaseButton label="Button" icon={<Icon name="star" />} disabled />
      <BaseButton
        label="Button"
        fillColor={ColorsWIP.Dark}
        textColor={ColorsWIP.White}
        stroke={false}
        disabled
      />
      <BaseButton textColor={ColorsWIP.Dark} label="Button" fillColor="transparent" disabled />
    </Group>
  );
};
