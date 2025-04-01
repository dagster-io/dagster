// eslint-disable-next-line no-restricted-imports
import {Box, Caption, Colors, Tag} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {MaterializationTag} from './MaterializationTag';
import {Timestamp} from '../app/time/Timestamp';
import {StatusCase} from '../asset-graph/AssetNodeStatusContent';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {LiveDataForNode} from '../asset-graph/Utils';
import {StatusCaseDot} from '../asset-graph/sidebar/util';
import {titleForRun} from '../runs/RunUtils';
import {AssetViewDefinitionNodeFragment} from './types/AssetView.types';

/** We explicitly don't want to share partition-level information with stakeholders,
 * so this status component exposes only basic "materializing, success, failed, missing"
 * states.
 */
export const SimpleStakeholderAssetStatus = ({
  liveData,
  assetNode,
  partition,
}: {
  liveData: LiveDataForNode | undefined;
  assetNode: Pick<AssetViewDefinitionNodeFragment, 'assetKey' | 'isObservable'>;
  partition: string | null;
}) => {
  if (!liveData) {
    return <span />;
  }

  if ((liveData.inProgressRunIds || []).length > 0) {
    return (
      <Caption>
        Materializing in{' '}
        <AssetRunLink assetKey={assetNode.assetKey} runId={liveData.inProgressRunIds[0]!} />
      </Caption>
    );
  }

  if (liveData.runWhichFailedToMaterialize) {
    return (
      <Tag intent="danger">
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <StatusCaseDot statusCase={StatusCase.FAILED_MATERIALIZATION} />
          Failed in
          <AssetRunLink
            assetKey={assetNode.assetKey}
            runId={liveData.runWhichFailedToMaterialize.id}
          >
            <Box style={{color: Colors.textRed()}}>
              {titleForRun(liveData.runWhichFailedToMaterialize)}
            </Box>
          </AssetRunLink>
        </Box>
      </Tag>
    );
  }
  const partitionTag = partition ? (
    <Tag intent="none">
      <Link to={`?view=partitions&partition=${encodeURIComponent(partition)}`}>
        <Caption color={Colors.textDefault()}>{partition}</Caption>
      </Link>
    </Tag>
  ) : undefined;

  if (liveData.lastMaterialization) {
    return (
      <Box flex={{gap: 4}}>
        <MaterializationTag
          assetKey={assetNode.assetKey}
          event={liveData.lastMaterialization}
          stepKey={liveData.stepKey}
        />
        {partitionTag}
      </Box>
    );
  }
  if (liveData.lastObservation && assetNode.isObservable) {
    return (
      <Box flex={{gap: 4}}>
        <Tag intent="none">
          <Timestamp timestamp={{ms: Number(liveData.lastObservation.timestamp)}} />
        </Tag>
        {partitionTag}
      </Box>
    );
  }

  return (
    <Caption color={Colors.textLighter()}>
      {assetNode.isObservable ? 'Never observed' : 'Never materialized'}
    </Caption>
  );
};
