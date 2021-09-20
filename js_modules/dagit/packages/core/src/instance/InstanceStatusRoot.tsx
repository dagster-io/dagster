import * as React from 'react';
import {Route, Switch} from 'react-router-dom';

import {Group} from '../ui/Group';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {InstanceBackfills} from './InstanceBackfills';
import {InstanceConfig} from './InstanceConfig';
import {InstanceHealthPage} from './InstanceHealthPage';
import {InstanceSchedules} from './InstanceSchedules';
import {InstanceSensors} from './InstanceSensors';

export const InstanceStatusRoot = () => {
  return (
    <Page>
      <Group direction="column" spacing={12}>
        <PageHeader title={<Heading>Instance status</Heading>} />
        <Switch>
          <Route path="/instance/health" render={() => <InstanceHealthPage />} />
          <Route path="/instance/schedules" render={() => <InstanceSchedules />} />
          <Route path="/instance/sensors" render={() => <InstanceSensors />} />
          <Route path="/instance/backfills" render={() => <InstanceBackfills />} />
          <Route path="/instance/config" render={() => <InstanceConfig />} />
        </Switch>
      </Group>
    </Page>
  );
};
