import {Meta} from '@storybook/react';

import {SpinnerWithText} from '../SpinnerWithText';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'SpinnerWithText',
  component: SpinnerWithText,
} as Meta;

export const Default = () => {
  return <SpinnerWithText label="Hey kid I'm a computer" />;
};
