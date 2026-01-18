import {Box, Colors, Icon} from '@dagster-io/ui-components';
import React from 'react';

import {AssetNodeRowBox} from './AssetNode';
import {AssetLatestRunSpinner, AssetRunLink} from './AssetRunLinking';
import {LiveDataForNode} from './Utils';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthSummaryPopover, statusToIconAndColor} from '../assets/AssetHealthSummary';
import {titleForRun} from '../runs/RunUtils';
import {AssetNodeFragment} from './types/AssetNode.types';

export const AssetNodeHealthRow = ({
  definition,
  liveData,
}: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  const {liveData: healthData} = useAssetHealthData(definition.assetKey);
  const health = healthData?.assetHealth;

  const {inProgressRunIds, unstartedRunIds, partitionStats} = liveData || {};
  const materializingRunId = inProgressRunIds?.[0] || unstartedRunIds?.[0];
  const numMaterializing = partitionStats?.numMaterializing;

  const {iconName, iconColor, backgroundColor, textColor, text} = React.useMemo(() => {
    return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
  }, [health]);

  if (materializingRunId) {
    return (
      <AssetNodeRowBox
        padding={{horizontal: 8}}
        background={Colors.backgroundBlue()}
        flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
      >
        <Box flex={{gap: 6, alignItems: 'center'}}>
          <AssetLatestRunSpinner liveData={liveData} purpose="caption-text" />
          <span style={{color: Colors.textBlue()}}>
            {numMaterializing === 1
              ? `Executing 1 partition...`
              : numMaterializing
                ? `Executing ${numMaterializing} partitions...`
                : `Executing...`}
          </span>
        </Box>
        {!numMaterializing || numMaterializing === 1 ? (
          <AssetRunLink assetKey={definition.assetKey} runId={materializingRunId}>
            <span>Run {titleForRun({id: materializingRunId})}</span>
          </AssetRunLink>
        ) : undefined}
      </AssetNodeRowBox>
    );
  }

  return (
    <AssetNodeRowBox
      padding={{horizontal: 8}}
      background={materializingRunId ? Colors.backgroundBlue() : backgroundColor}
      flex={{justifyContent: 'flex-start', alignItems: 'center', gap: 6}}
    >
      <AssetHealthSummaryPopover health={health} assetKey={definition.assetKey}>
        <Icon name={iconName} color={iconColor} />
      </AssetHealthSummaryPopover>
      <span style={{color: textColor}}>{text}</span>
    </AssetNodeRowBox>
  );
};
