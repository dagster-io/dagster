import faker from 'faker';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {DeletionDialog, Props as DeletionDialogProps} from '../DeletionDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DeletionDialog',
  component: DeletionDialog,
};

const Template = (props: DeletionDialogProps) => (
  <StorybookProvider>
    <DeletionDialog {...props} />
  </StorybookProvider>
);

const ids = [
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
];

export const Success = {
  render: (args: DeletionDialogProps) => <Template {...args} />,
  args: {
    isOpen: true,
    onClose: () => {
      console.log('Close!');
    },
    onComplete: () => {
      console.log('Complete!');
    },
    onTerminateInstead: () => {
      console.log('Terminate instead!');
    },
    selectedRuns: ids.reduce((accum, id) => ({...accum, [id]: true}), {}),
  },
};

export const WithError = {
  render: (args: DeletionDialogProps) => <Template {...args} />,
  args: {
    isOpen: true,
    onClose: () => {
      console.log('Close!');
    },
    onComplete: () => {
      console.log('Complete!');
    },
    onTerminateInstead: () => {
      console.log('Terminate instead!');
    },
    selectedRuns: ids.reduce((accum, id) => ({...accum, [id]: true}), {}),
  },
};
