import {Box, Spinner, Tabs} from '@dagster-io/ui-components';

import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {AutomaterializeDot} from '../assets/auto-materialization/AutomaterializeDot';
import {useAutomaterializeDaemonStatus} from '../assets/useAutomaterializeDaemonStatus';
import {TabLink} from '../ui/TabLink';

interface Props {
  tab: string;
}

export const AutomationTabs = (props: Props) => {
  const {tab} = props;

  const automaterialize = useAutomaterializeDaemonStatus();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
      <Tabs selectedTabId={tab}>
        <TabLink id="schedules" title="Schedules" to="/automation/schedules" />
        <TabLink id="sensors" title="Sensors" to="/automation/sensors" />
        {automaterializeSensorsFlagState === 'has-global-amp' ? (
          <TabLink
            id="amp"
            title={
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <div>Auto-materialize</div>
                {automaterialize.loading ? (
                  <Spinner purpose="body-text" />
                ) : (
                  <AutomaterializeDot $paused={automaterialize.paused} />
                )}
              </Box>
            }
            to="/automation/auto-materialize"
          />
        ) : null}
        <TabLink id="backfills" title="Backfills" to="/automation/backfills" />
      </Tabs>
    </Box>
  );
};
