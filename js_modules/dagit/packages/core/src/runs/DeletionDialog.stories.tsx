import {Story, Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';

import {DeletionDialog, Props as DeletionDialogProps} from './DeletionDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'DeletionDialog',
  component: DeletionDialog,
} as Meta;

const Template: Story<DeletionDialogProps & {mocks?: any}> = ({mocks, ...props}) => (
  <StorybookProvider apolloProps={{mocks}}>
    <DeletionDialog {...props} />
  </StorybookProvider>
);

const ids = [
  faker.random.uuid().slice(0, 8),
  faker.random.uuid().slice(0, 8),
  faker.random.uuid().slice(0, 8),
];

export const Success = Template.bind({});
Success.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
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
};

export const WithError = Template.bind({});
WithError.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
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
};
