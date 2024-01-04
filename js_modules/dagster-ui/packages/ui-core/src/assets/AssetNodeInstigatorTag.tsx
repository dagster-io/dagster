import {gql} from '@apollo/client';
import flatMap from 'lodash/flatMap';
import uniqBy from 'lodash/uniqBy';
import React from 'react';

import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {RepoAddress} from '../workspace/types';

import {useAutomationPolicySensorFlag} from './AutomationPolicySensorFlag';
import {AssetNodeInstigatorsFragment} from './types/AssetNodeInstigatorTag.types';

export const AssetNodeInstigatorTag = ({
  assetNode,
  repoAddress,
}: {
  assetNode: AssetNodeInstigatorsFragment;
  repoAddress: RepoAddress;
}) => {
  const automaterializeSensorsFlagState = useAutomationPolicySensorFlag();
  const {schedules, sensors} = React.useMemo(() => {
    const schedules = uniqBy(
      flatMap(assetNode.jobs, (j) => j.schedules),
      'id',
    );
    const sensors = uniqBy(
      flatMap(assetNode.jobs, (j) => j.sensors),
      'id',
    );

    if (automaterializeSensorsFlagState === 'has-sensor-amp') {
      const ampSensor = assetNode.automationPolicySensor;
      if (ampSensor) {
        sensors.push(ampSensor);
      }
    }

    return {schedules, sensors};
  }, [assetNode, automaterializeSensorsFlagState]);

  return (
    <ScheduleOrSensorTag
      repoAddress={repoAddress}
      schedules={schedules}
      sensors={sensors}
      showSwitch={false}
    />
  );
};

export const ASSET_NODE_INSTIGATORS_FRAGMENT = gql`
  fragment AssetNodeInstigatorsFragment on AssetNode {
    id
    jobs {
      id
      name
      schedules {
        id
        ...ScheduleSwitchFragment
      }
      sensors {
        id
        ...SensorSwitchFragment
      }
    }
    automationPolicySensor {
      id
      ...SensorSwitchFragment
    }
  }

  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
