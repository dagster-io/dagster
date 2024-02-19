import {Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {useAutomaterializeDaemonStatus} from './useAutomaterializeDaemonStatus';

export const AutomaterializeDaemonStatusTag = () => {
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <Tooltip
      content={
        paused
          ? 'Auto-materializing is paused. New materializations will not be triggered by auto-materialization policies.'
          : ''
      }
      canShow={paused}
    >
      <Link to="/health" style={{outline: 'none'}}>
        <Tag icon={paused ? 'toggle_off' : 'toggle_on'} intent={paused ? 'warning' : 'success'}>
          {paused ? 'Auto-materialize off' : 'Auto-materialize on'}
        </Tag>
      </Link>
    </Tooltip>
  );
};
