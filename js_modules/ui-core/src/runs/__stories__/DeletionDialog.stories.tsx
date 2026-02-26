import faker from 'faker';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {DeletionDialog, Props as DeletionDialogProps} from '../DeletionDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DeletionDialog',
  component: DeletionDialog,
};

const Template = ({mocks, ...props}: DeletionDialogProps & {mocks?: any}) => (
  <StorybookProvider apolloProps={{mocks}}>
    <DeletionDialog {...props} />
  </StorybookProvider>
);

const ids = [
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
];

export const Success = {
  render: (args: DeletionDialogProps & {mocks?: any}) => <Template {...args} />,
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
    mocks: {
      Mutation: () => ({
        deletePipelineRun: () => ({
          __typename: 'DeletePipelineRunSuccess',
        }),
      }),
    },
  },
};

export const WithError = {
  render: (args: DeletionDialogProps & {mocks?: any}) => <Template {...args} />,
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
    mocks: {
      Mutation: () => ({
        deletePipelineRun: (args: {runId: string}) => {
          // Fail the last run
          if (args.runId === ids[2]) {
            return {
              __typename: 'PythonError',
              message: 'Oh no!',
            };
          }
          return {
            __typename: 'DeletePipelineRunSuccess',
          };
        },
      }),
    },
  },
};
