import flatMap from 'lodash/flatMap';
import React from 'react';

import {graphql} from '../graphql';
import {AssetNodeInstigatorsFragmentFragment} from '../graphql/graphql';
import {ScheduleOrSensorTag} from '../nav/ScheduleOrSensorTag';
import {RepoAddress} from '../workspace/types';

export const AssetNodeInstigatorTag: React.FC<{
  assetNode: AssetNodeInstigatorsFragmentFragment;
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

export const ASSET_NODE_INSTIGATORS_FRAGMENT = graphql(`
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
`);
