import {Box, Caption, Colors, Tag, Tooltip} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {useAutomaterializeDaemonStatus} from './useAutomaterializeDaemonStatus';

export const AutomaterializeDaemonStatusTagLegacy = () => {
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

export const AutomaterializeDaemonStatusTag = () => {
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
      <Tooltip
        content={
          paused ? (
            <Box flex={{direction: 'column'}}>
              <span>Sensor is paused.</span>{' '}
              <span>New materializations will not be triggered by automation policies.</span>
            </Box>
          ) : (
            'asset_automation_sensor is running, evaluates every 30s'
          )
        }
        canShow={paused}
      >
        <div>
          <Tag icon="automator" animatedIcon={paused} intent={paused ? 'warning' : 'primary'}>
            <Link to="/overview/automaterialize" style={{outline: 'none'}}>
              {' '}
              my_sensor_name{' '}
            </Link>
          </Tag>
        </div>
      </Tooltip>
      <Caption style={{color: Colors.textDisabled()}}>
        {paused ? 'Paused. Not evaluating' : 'Evaluating every 30 seconds'}
      </Caption>
    </Box>
  );
};
export const AutomaterializeDaemonStatusTag2 = () => {
  const {paused} = useAutomaterializeDaemonStatus();

  return (
    <Box flex={{direction: 'column', gap: 4}} style={{flex: 1}}>
      <Tooltip
        content={
          paused ? (
            <Box flex={{direction: 'column'}}>
              <span>asset_automation_sensor is paused.</span>{' '}
              <span>New materializations will not be triggered by automation policies.</span>
            </Box>
          ) : (
            'asset_automation_sensor is running, evaluates every 30s'
          )
        }
        canShow={paused}
      >
        <div>
          <Tag icon="sensors" intent={paused ? 'warning' : 'primary'}>
            {paused ? 'Paused' : 'Running'}
          </Tag>
        </div>
      </Tooltip>
      <Caption style={{color: Colors.textLight()}}>
        Targeted by{' '}
        <Link to="/overview/automaterialize" style={{outline: 'none'}}>
          {' '}
          my_sensor_name{' '}
        </Link>
      </Caption>
    </Box>
  );
};
