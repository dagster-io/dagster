import {Meta} from '@storybook/react';

import {CoreColors} from '../../palettes/CoreColors';
import {BaseButton} from '../BaseButton';
import {Box} from '../Box';
import {Colors} from '../Color';
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
      <BaseButton label="Button" fillColor={Colors.accentGray()} textColor={Colors.alwaysWhite()} />
      <BaseButton
        label="Button"
        fillColor={Colors.accentBlue()}
        textColor={Colors.alwaysWhite()}
        icon={<Icon name="star" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.accentGreen()}
        textColor={Colors.alwaysWhite()}
        rightIcon={<Icon name="close" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.accentRed()}
        textColor={Colors.alwaysWhite()}
        icon={<Icon name="source" />}
        rightIcon={<Icon name="expand_more" />}
      />
      <BaseButton
        label="Button"
        fillColor={Colors.accentOlive()}
        textColor={Colors.alwaysWhite()}
        icon={<Icon name="folder_open" />}
      />
      <BaseButton
        fillColor={Colors.accentYellow()}
        textColor={Colors.alwaysWhite()}
        icon={<Icon name="cached" />}
      />
    </Group>
  );
};

export const Transparent = () => {
  return (
    <Box padding={12} background={Colors.backgroundGray()}>
      <Group direction="column" spacing={8}>
        <BaseButton textColor={Colors.accentGray()} label="Button" fillColor="transparent" />
        <BaseButton
          textColor={Colors.accentGray()}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="star" />}
        />
        <BaseButton
          textColor={Colors.accentGray()}
          label="Button"
          fillColor="transparent"
          rightIcon={<Icon name="close" />}
        />
        <BaseButton
          textColor={Colors.accentGray()}
          label="Button"
          fillColor="transparent"
          icon={<Icon name="source" />}
          rightIcon={<Icon name="expand_more" />}
        />
        <BaseButton
          textColor={Colors.accentGray()}
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
