import {Box, Colors, Icon} from '@dagster-io/ui-components';

import {AssetNodeRow} from './AssetNode';
import {labelForFacet} from './AssetNodeFacets';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {LiveDataForNode} from './Utils';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {statusToIconAndColor} from '../assets/AssetHealthSummary';
import {AssetNodeFragment} from './types/AssetNode.types';
import {humanizedMinutesLateString, isAssetOverdue} from '../assets/OverdueTag';
import {TimeFromNow} from '../ui/TimeFromNow';

export const AssetNodeFreshnessRow = ({
  definition,
  liveData,
}: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  const {liveData: healthData} = useAssetHealthData(definition.assetKey);
  const health = healthData?.assetHealth;

  const freshnessStatus =
    definition.freshnessStatusInfo?.freshnessStatus ?? health?.freshnessStatus;
  const lastMaterializedTimestamp =
    definition.freshnessStatusInfo?.freshnessStatusMetadata?.lastMaterializedTimestamp ?? null;
  if (!freshnessStatus) {
    return <AssetNodeFreshnessRowOld liveData={liveData} />;
  }

  const {iconColor, subStatusIconName, text2} = statusToIconAndColor[freshnessStatus];

  return (
    <AssetNodeRow label={labelForFacet(AssetNodeFacet.Freshness)}>
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <Icon name={subStatusIconName} color={iconColor} />
        {text2}
        {lastMaterializedTimestamp !== null ? (
          <TimeFromNow unixTimestamp={lastMaterializedTimestamp} showTooltip={false} />
        ) : null}
      </Box>
    </AssetNodeRow>
  );
};

export const AssetNodeFreshnessRowOld = ({liveData}: {liveData: LiveDataForNode | undefined}) => {
  return (
    <AssetNodeRow label={labelForFacet(AssetNodeFacet.Freshness)}>
      {!liveData?.freshnessInfo ? null : isAssetOverdue(liveData) ? (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <Icon name="close" color={Colors.accentRed()} />
          {humanizedMinutesLateString(liveData.freshnessInfo.currentMinutesLate ?? 0)}
        </Box>
      ) : (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          <Icon name="done" color={Colors.accentGreen()} />
          Passing
        </Box>
      )}
    </AssetNodeRow>
  );
};
