import {gql} from '@apollo/client';
import {useMemo} from 'react';

import {AssetNodeInstigatorsFragment} from './types/AssetNodeInstigatorTag.types';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {SCHEDULE_SWITCH_FRAGMENT} from '../schedules/ScheduleSwitch';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitch.types';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitch.types';
import {RepoAddress} from '../workspace/types';

export const AssetNodeInstigatorTag = ({
  assetNode,
  repoAddress,
}: {
  assetNode: AssetNodeInstigatorsFragment;
  repoAddress: RepoAddress;
}) => {
  const {schedules, sensors} = useMemo(() => {
    const instigators = assetNode.targetingInstigators;
    const schedules = instigators.filter(
      (instigator): instigator is ScheduleSwitchFragment => instigator.__typename === 'Schedule',
    );
    const sensors = instigators.filter(
      (instigator): instigator is SensorSwitchFragment => instigator.__typename === 'Sensor',
    );

    return {schedules, sensors};
  }, [assetNode]);

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
    targetingInstigators {
      ... on Schedule {
        ...ScheduleSwitchFragment
      }
      ... on Sensor {
        ...SensorSwitchFragment
      }
    }
  }
  ${SCHEDULE_SWITCH_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
