import {Button} from '@blueprintjs/core';
import React from 'react';

import {TimezoneSelect} from './TimezoneSelect';
import {automaticLabel} from './browserTimezone';

export const DarkTimezonePicker = React.memo(() => {
  const trigger = React.useCallback(
    (timezone: string) => (
      <Button small text={timezone === 'Automatic' ? automaticLabel() : timezone} icon="time" />
    ),
    [],
  );

  return (
    <div className="bp3-dark" style={{padding: 5, flexShrink: 0}}>
      <TimezoneSelect trigger={trigger} />
    </div>
  );
});
