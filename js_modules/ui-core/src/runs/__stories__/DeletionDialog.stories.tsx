import {MockedProvider} from '@apollo/client/testing';
import faker from 'faker';

import {DeletionDialog, Props as DeletionDialogProps} from '../DeletionDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DeletionDialog',
  component: DeletionDialog,
};

const Template = (props: DeletionDialogProps) => (
  <MockedProvider>
    <DeletionDialog {...props} />
  </MockedProvider>
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
