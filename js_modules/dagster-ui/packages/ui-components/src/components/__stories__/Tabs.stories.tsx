import {Meta} from '@storybook/react';
import {useState} from 'react';

import {Colors} from '../Color';
import {Group} from '../Group';
import {Icon} from '../Icon';
import {Tab, Tabs} from '../Tabs';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Tabs',
  component: Tabs,
} as Meta;

export const Default = () => {
  const [tab, setTab] = useState('health');
  return (
    <Group spacing={0} direction="column">
      <Tabs selectedTabId={tab} onChange={setTab}>
        <Tab id="health" title="Health" />
        <Tab id="schedules" title="Schedules" count={2} />
        <Tab
          id="sensors"
          title="Sensors"
          icon={<Icon name="warning" color={Colors.accentYellow()} />}
        />
        <Tab id="backfills" title="Backfills" disabled />
        <Tab id="config" title={<a href="/?path=/story/box">Box Component</a>} />
      </Tabs>
      <Tabs small selectedTabId={tab} onChange={setTab}>
        <Tab id="health" title="Health" />
        <Tab id="schedules" title="Schedules" count={2} disabled />
        <Tab
          id="sensors"
          title="Sensors"
          disabled
          icon={<Icon name="warning" color={Colors.accentYellow()} />}
        />
        <Tab id="backfills" title="Backfills" disabled />
        <Tab id="config" disabled title={<a href="/?path=/story/box">Box Component</a>} />
      </Tabs>
    </Group>
  );
};
