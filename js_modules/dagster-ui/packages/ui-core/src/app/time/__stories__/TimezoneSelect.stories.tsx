import {Button, Icon} from '@dagster-io/ui-components';
import {Meta, StoryFn} from '@storybook/nextjs';
import {useState} from 'react';

import {TimezoneSelect} from '../TimezoneSelect';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TimezoneSelect',
  component: TimezoneSelect,
} as Meta<typeof TimezoneSelect>;

export const Default: StoryFn<typeof TimezoneSelect> = () => {
  const [timezone, setTimezone] = useState('America/New_York');
  return (
    <div style={{width: '300px'}}>
      <TimezoneSelect
        timezone={timezone}
        setTimezone={setTimezone}
        trigger={() => (
          <Button
            rightIcon={<Icon name="arrow_drop_down" />}
            style={{minWidth: '200px', display: 'flex', justifyContent: 'space-between'}}
          >
            {timezone}
          </Button>
        )}
        includeAutomatic={false}
      />
    </div>
  );
};
