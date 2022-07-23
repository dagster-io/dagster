import {gql} from '@apollo/client';
import flatMap from 'lodash/flatMap';
import React from 'react';

import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {RepoAddress} from '../workspace/types';

import {AssetNodeInstigatorsFragment} from './types/AssetNodeInstigatorsFragment';

export const AssetNodeInstigatorTag: React.FC<{
  assetNode: AssetNodeInstigatorsFragment;
  repoAddress: RepoAddress;
}> = ({assetNode, repoAddress}) => {
  const schedules = flatMap(assetNode.jobs, (j) => j.schedules);
  const sensors = flatMap(assetNode.jobs, (j) => j.sensors);

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
        __typename
        ...ScheduleSwitchFragment
      }
      sensors {
        id
        __typename
        ...SensorSwitchFragment
      }
    }
  }
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
