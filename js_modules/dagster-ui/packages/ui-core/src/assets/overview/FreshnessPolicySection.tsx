import {BodySmall, Box, Colors, Popover, Skeleton, Tag} from '@dagster-io/ui-components';
import dayjs from 'dayjs';

import {useAssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetKey} from '../types';
import {AssetTableDefinitionFragment} from '../types/AssetTableFragment.types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';

export const FreshnessPolicySection = ({
  cachedOrLiveAssetNode,
  policy,
}: {
  assetNode: AssetViewDefinitionNodeFragment | null | undefined;
  cachedOrLiveAssetNode: AssetViewDefinitionNodeFragment | AssetTableDefinitionFragment;
  policy: NonNullable<AssetViewDefinitionNodeFragment['internalFreshnessPolicy']>;
}) => {
  const {liveData} = useAssetHealthData(cachedOrLiveAssetNode.assetKey);

  if (!liveData) {
    return <Skeleton $width="100%" $height={24} />;
  }

  const freshnessStatus = liveData?.assetHealth?.freshnessStatus;

  const metadata = liveData?.assetHealth?.freshnessStatusMetadata;

  const lastMaterializedTimestamp = metadata?.lastMaterializedTimestamp;

  const {iconName2, intent, text2} = statusToIconAndColor[freshnessStatus ?? 'undefined'];

  return (
    <Box flex={{direction: 'column'}}>
      <Box
        border="bottom"
        padding={{bottom: 12}}
        margin={{bottom: 12}}
        flex={{gap: 8, direction: 'column'}}
      >
        <div>
          <Tag intent={intent} icon={iconName2}>
            {text2}
          </Tag>
        </div>
        {lastMaterializedTimestamp ? (
          <BodySmall color={Colors.textLight()}>
            Last materialized {dayjs(Number(lastMaterializedTimestamp * 1000)).fromNow()}
          </BodySmall>
        ) : (
          <BodySmall color={Colors.textLight()}>No materializations</BodySmall>
        )}
      </Box>
      <Box flex={{direction: 'column', gap: 4}}>
        <BodySmall color={Colors.textLight()}>
          Fails if more than {dayjs.duration(policy.failWindowSeconds, 'seconds').humanize()} since
          last materialization
        </BodySmall>
        {policy.warnWindowSeconds ? (
          <BodySmall color={Colors.textLight()}>
            Warns if more than {dayjs.duration(policy.warnWindowSeconds, 'seconds').humanize()}{' '}
            since last materialization
          </BodySmall>
        ) : null}
      </Box>
    </Box>
  );
};

export const FreshnessTag = ({
  policy,
  assetKey,
}: {
  policy: NonNullable<AssetViewDefinitionNodeFragment['internalFreshnessPolicy']>;
  assetKey: AssetKey;
}) => {
  const {liveData} = useAssetHealthData(assetKey);

  if (!liveData) {
    return <Skeleton $width="100%" $height={24} />;
  }

  const freshnessStatus = liveData?.assetHealth?.freshnessStatus;

  const metadata = liveData?.assetHealth?.freshnessStatusMetadata;

  const lastMaterializedTimestamp = metadata?.lastMaterializedTimestamp;

  const {iconName2, intent, text2} = statusToIconAndColor[freshnessStatus ?? 'undefined'];

  return (
    <div>
      <Popover
        interactionKind="hover"
        content={
          <div>
            <Box padding={{vertical: 8, horizontal: 12}}>
              {lastMaterializedTimestamp ? (
                <BodySmall>
                  Last materialized {dayjs(Number(lastMaterializedTimestamp * 1000)).fromNow()}
                </BodySmall>
              ) : (
                <BodySmall>No materializations</BodySmall>
              )}
            </Box>
            <Box flex={{direction: 'column', gap: 4}} padding={{vertical: 8, horizontal: 12}}>
              <BodySmall color={Colors.textLight()}>
                Fails if more than {dayjs.duration(policy.failWindowSeconds, 'seconds').humanize()}{' '}
                since last materialization
              </BodySmall>
              {policy.warnWindowSeconds ? (
                <BodySmall color={Colors.textLight()}>
                  Warns if more than{' '}
                  {dayjs.duration(policy.warnWindowSeconds, 'seconds').humanize()} since last
                  materialization
                </BodySmall>
              ) : null}
            </Box>
          </div>
        }
      >
        <Tag intent={intent} icon={iconName2}>
          {text2}
        </Tag>
      </Popover>
    </div>
  );
};
