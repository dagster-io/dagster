import {gql} from '@apollo/client';
import flatMap from 'lodash/flatMap';
import React from 'react';

import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {RepoAddress} from '../workspace/types';

import {AssetNodeInstigatorsFragment} from './types/AssetNodeInstigatorTag.types';

export const AssetNodeInstigatorTag = ({
  assetNode,
  repoAddress,
}: {
  assetNode: AssetNodeInstigatorsFragment;
  repoAddress: RepoAddress;
}) => {
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

        ...ScheduleSwitchFragment
      }
      sensors {
        id

        ...SensorSwitchFragment
      }
    }
  }

  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
