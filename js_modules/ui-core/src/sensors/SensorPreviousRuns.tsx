import * as React from 'react';

import {RunsFeedTableWithFilters} from '../runs/RunsFeedTable';
import {SensorFragment} from './types/SensorFragment.types';
import {DagsterTag} from '../runs/RunTag';
import {repoAddressAsTag} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

export const SensorPreviousRuns = ({
  sensor,
  repoAddress,
  tabs,
}: {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  tabs?: React.ReactElement;
}) => {
  const filter = React.useMemo(
    () => ({
      tags: [
        {key: DagsterTag.SensorName, value: sensor.name},
        {key: DagsterTag.RepositoryLabelTag, value: repoAddressAsTag(repoAddress)},
      ],
    }),
    [repoAddress, sensor.name],
  );
  return (
    <RunsFeedTableWithFilters filter={filter} includeRunsFromBackfills actionBarComponents={tabs} />
  );
};
