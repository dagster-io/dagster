import {Box, Colors, Spinner, Tabs} from '@dagster-io/ui-components';

import {useAutoMaterializeSensorFlag} from '../assets/AutoMaterializeSensorFlag';
import {useAutomaterializeDaemonStatus} from '../assets/useAutomaterializeDaemonStatus';
import {TabLink} from '../ui/TabLink';

interface Props {
  tab: 'schedules-and-sensors' | 'global-amp';
}

export const AutomationTabs = (props: Props) => {
  const {tab} = props;

  const automaterialize = useAutomaterializeDaemonStatus();
  const automaterializeSensorsFlagState = useAutoMaterializeSensorFlag();

  return (
    <Tabs selectedTabId={tab}>
      <TabLink id="schedules-and-sensors" title="定时任务和监控器" to="/automation" />
      {automaterializeSensorsFlagState === 'has-global-amp' ? (
        <TabLink
          id="global-amp"
          title={
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <div>自动物化</div>
              {automaterialize.loading ? (
                <Spinner purpose="body-text" />
              ) : (
                <div
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor:
                      automaterialize.paused === false ? Colors.accentBlue() : Colors.accentGray(),
                  }}
                />
              )}
            </Box>
          }
          to="/overview/automation"
        />
      ) : null}
    </Tabs>
  );
};
