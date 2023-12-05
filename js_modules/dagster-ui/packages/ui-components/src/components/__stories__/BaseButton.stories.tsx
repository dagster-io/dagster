import {Meta} from '@storybook/react';
import * as React from 'react';

import {CoreColors} from '../../palettes/Colors';
import {BaseButton} from '../BaseButton';
import {Box} from '../Box';
import {Group} from '../Group';
import {Icon} from '../Icon';

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
      <BaseButton label="Button" fillColor={CoreColors.Gray900} textColor={CoreColors.White} />
      <BaseButton
        label="Button"
        fillColor={CoreColors.Blue500}
        textColor={CoreColors.White}
        icon={<Icon name="star" />}
      />
      <BaseButton
        label="Button"
        fillColor={CoreColors.Green500}
        textColor={CoreColors.White}
        rightIcon={<Icon name="close" />}
      />
      <BaseButton
        label="Button"
        fillColor={CoreColors.Red500}
        textColor={CoreColors.White}
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      />
      <BaseButton
        label="Button"
        fillColor={CoreColors.Olive500}
        textColor={CoreColors.White}
        icon={<Icon name="folder_open" />}
      />
      <BaseButton
        fillColor={CoreColors.Yellow500}
        textColor={CoreColors.White}
        icon={<Icon name="cached" />}
      />
    </Group>
  );
};

export const Transparent = () => {
  return (
    <Box padding={12} background={CoreColors.Gray200}>
      <Group direction="column" spacing={8}>
        <BaseButton textColor={CoreColors.Gray900} label="Button" fillColor="transparent" />
        <BaseButton
          textColor={CoreColors.Gray900}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="star" />}
        />
        <BaseButton
          textColor={CoreColors.Gray900}
          label="Button"
          fillColor="transparent"
          rightIcon={<Icon name="close" />}
        />
        <BaseButton
          textColor={CoreColors.Gray900}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="source" />}
          rightIcon={<Icon name="expand_more" />}
        />
        <BaseButton
          textColor={CoreColors.Gray900}
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
        fillColor={CoreColors.Gray900}
        textColor={CoreColors.White}
        disabled
      />
      <BaseButton textColor={CoreColors.Gray900} label="Button" fillColor="transparent" disabled />
    </Group>
  );
};
