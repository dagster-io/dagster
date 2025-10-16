import {StoryFn} from '@storybook/nextjs';
import faker from 'faker';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {TerminationDialog, Props as TerminationDialogProps} from '../TerminationDialog';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TerminationDialog',
  component: TerminationDialog,
};

const Template: StoryFn<TerminationDialogProps> = (props) => (
  <StorybookProvider>
    <TerminationDialog {...props} />
  </StorybookProvider>
);

const runIDs = [
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
  faker.datatype.uuid().slice(0, 8),
];

export const ForceTerminationCheckbox = Template.bind({});
ForceTerminationCheckbox.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
  },
  selectedRuns: {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[0]!]: true,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[1]!]: false,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[2]!]: true,
  },
};

export const ForceTerminationNoCheckbox = Template.bind({});
ForceTerminationNoCheckbox.args = {
  isOpen: true,
  onClose: () => {
    console.log('Close!');
  },
  selectedRuns: {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[0]!]: false,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[1]!]: false,
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    [runIDs[2]!]: false,
  },
};
