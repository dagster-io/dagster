// js_modules/dagster-ui/packages/ui-core/src/runs/RunAlertNotifications.oss.tsx
import {Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';

export const RunAlertNotifications = ({runId}: {runId: string}) => {
  const [subscribed, setSubscribed] = useState(false);

  const label = subscribed ? 'Notifications ' : 'Notify on completion';
  const icon = subscribed ? 'success' : 'notifications';

  return (
    <Tooltip content={subscribed ? 'You will be notified when this run completes' : undefined}>
      <Button
        icon={<Icon name={icon} />}
        onClick={() => {
          setSubscribed((v) => !v);
          console.log('Toggled notify-on-completion for run', runId);
        }}
      >
        {label}
      </Button>
    </Tooltip>
  );
};