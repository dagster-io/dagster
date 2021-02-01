import {Button} from '@blueprintjs/core';
import React from 'react';

import {TimezoneSelect} from 'src/app/time/TimezoneSelect';
import {automaticLabel} from 'src/app/time/browserTimezone';

export const DarkTimezonePicker: React.FC = () => {
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
};
