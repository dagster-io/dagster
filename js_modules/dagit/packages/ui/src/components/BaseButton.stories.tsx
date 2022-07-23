import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {BaseButton} from './BaseButton';
import {Box} from './Box';
import {Colors} from './Colors';
import {Group} from './Group';
import {Icon} from './Icon';

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
      <BaseButton label="Button" fillColor={Colors.Dark} textColor={Colors.White} />
      <BaseButton
        label="Button"
        fillColor={Colors.Blue500}
        textColor={Colors.White}
        icon={<Icon name="star" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.Green500}
        textColor={Colors.White}
        rightIcon={<Icon name="close" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.Red500}
        textColor={Colors.White}
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.Olive500}
        textColor={Colors.White}
        icon={<Icon name="folder_open" />}
      />
      <BaseButton
        fillColor={Colors.Yellow500}
        textColor={Colors.White}
        icon={<Icon name="cached" />}
      />
    </Group>
  );
};

export const Transparent = () => {
  return (
    <Box padding={12} background={Colors.Gray200}>
      <Group direction="column" spacing={8}>
        <BaseButton textColor={Colors.Dark} label="Button" fillColor="transparent" />
        <BaseButton
          textColor={Colors.Dark}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="star" />}
        />
        <BaseButton
          textColor={Colors.Dark}
          label="Button"
          fillColor="transparent"
          rightIcon={<Icon name="close" />}
        />
        <BaseButton
          textColor={Colors.Dark}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="source" />}
          rightIcon={<Icon name="expand_more" />}
        />
        <BaseButton textColor={Colors.Dark} fillColor="transparent" icon={<Icon name="cached" />} />
      </Group>
    </Box>
  );
};

export const Disabled = () => {
  return (
    <Group direction="column" spacing={8}>
      <BaseButton label="Button" icon={<Icon name="star" />} disabled />
      <BaseButton label="Button" fillColor={Colors.Dark} textColor={Colors.White} disabled />
      <BaseButton textColor={Colors.Dark} label="Button" fillColor="transparent" disabled />
    </Group>
  );
};
