import {BodySmall, Box, Colors, Popover, Skeleton, Tag} from '@dagster-io/ui-components';
import dayjs from 'dayjs';

import {useAssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {CronFreshnessPolicy, TimeWindowFreshnessPolicy} from '../../graphql/types';
import {humanCronString} from '../../schedules/humanCronString';
import {TimeFromNow} from '../../ui/TimeFromNow';
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
            Last materialized <TimeFromNow unixTimestamp={lastMaterializedTimestamp} />
          </BodySmall>
        ) : (
          <BodySmall color={Colors.textLight()}>No materializations</BodySmall>
        )}
      </Box>
      <Box flex={{direction: 'column', gap: 4}}>
        {policy.__typename === 'TimeWindowFreshnessPolicy' ? (
          <TimeWindowFreshnessPolicyDetails policy={policy} />
        ) : (
          <CronFreshnessPolicyDetails policy={policy} />
        )}
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
                  Last materialized <TimeFromNow unixTimestamp={lastMaterializedTimestamp} />
                </BodySmall>
              ) : (
                <BodySmall>No materializations</BodySmall>
              )}
            </Box>
            <Box flex={{direction: 'column', gap: 4}} padding={{vertical: 8, horizontal: 12}}>
              {policy.__typename === 'TimeWindowFreshnessPolicy' ? (
                <TimeWindowFreshnessPolicyDetails policy={policy} />
              ) : (
                <CronFreshnessPolicyDetails policy={policy} />
              )}
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

const TimeWindowFreshnessPolicyDetails = ({policy}: {policy: TimeWindowFreshnessPolicy}) => (
  <>
    <BodySmall color={Colors.textLight()}>
      Fails if more than {dayjs.duration(policy.failWindowSeconds, 'seconds').humanize()} since last
      materialization
    </BodySmall>
    {policy.warnWindowSeconds && (
      <BodySmall color={Colors.textLight()}>
        Warns if more than {dayjs.duration(policy.warnWindowSeconds, 'seconds').humanize()} since
        last materialization
      </BodySmall>
    )}
  </>
);

const CronFreshnessPolicyDetails = ({policy}: {policy: CronFreshnessPolicy}) => {
  const humanReadableDeadlineCron = policy.deadlineCron
    ? humanCronString(policy.deadlineCron, {
        longTimezoneName: policy.timezone || 'UTC',
      })
    : null;
  const humanReadableLowerBoundDelta = policy.lowerBoundDeltaSeconds
    ? dayjs.duration(policy.lowerBoundDeltaSeconds, 'seconds').humanize()
    : null;

  if (!humanReadableDeadlineCron || !humanReadableLowerBoundDelta) {
    return (
      <BodySmall color={Colors.textLight()}>
        Cron freshness policy configuration incomplete
      </BodySmall>
    );
  }

  return (
    <>
      <BodySmall color={Colors.textLight()}>Deadline: {humanReadableDeadlineCron}</BodySmall>
      <BodySmall color={Colors.textLight()}>
        Fresh if materialized no earlier than {humanReadableLowerBoundDelta} before each deadline.
      </BodySmall>
    </>
  );
};
