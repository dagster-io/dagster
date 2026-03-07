import {Button, Icon} from '@dagster-io/ui-components';
import {useState} from 'react';

import {TimezoneSelect} from '../TimezoneSelect';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TimezoneSelect',
  component: TimezoneSelect,
};

export const Default = {
  render: () => {
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
        />
      </div>
    );
  },
};
