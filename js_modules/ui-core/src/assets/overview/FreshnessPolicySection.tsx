import {Box, Popover, Skeleton, Tag, Text} from '@dagster-io/ui-components';
import dayjs from 'dayjs';

import {FRESHNESS_EVALUATION_ENABLED_QUERY, FRESHNESS_STATUS_QUERY} from './FreshnessQueries';
import {
  FreshnessEvaluationEnabledQuery,
  FreshnessEvaluationEnabledQueryVariables,
  FreshnessStatusQuery,
  FreshnessStatusQueryVariables,
} from './types/FreshnessQueries.types';
import {useQuery} from '../../apollo-client';
import {humanCronString} from '../../schedules/humanCronString';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {statusToIconAndColor} from '../AssetHealthSummary';
import {AssetKey} from '../types';
import {AssetViewDefinitionNodeFragment} from '../types/AssetView.types';
import {
  FreshnessPolicyFragment_CronFreshnessPolicy as CronFreshnessPolicy,
  FreshnessPolicyFragment,
  FreshnessPolicyFragment_TimeWindowFreshnessPolicy as TimeWindowFreshnessPolicy,
} from '../types/FreshnessPolicyFragment.types';

import '../../util/dayjsExtensions';

export interface FreshnessPolicySectionProps {
  assetKey: AssetKey;
  policy: FreshnessPolicyFragment;
}

export const FreshnessPolicySection = ({assetKey, policy}: FreshnessPolicySectionProps) => {
  const {data, loading} = useQuery<
    FreshnessEvaluationEnabledQuery,
    FreshnessEvaluationEnabledQueryVariables
  >(FRESHNESS_EVALUATION_ENABLED_QUERY);

  if (loading) {
    return <Skeleton $width="100%" $height={24} />;
  }

  return data?.instance?.freshnessEvaluationEnabled ? (
    <QueryfulFreshnessPolicySection assetKey={assetKey} policy={policy} />
  ) : (
    <FreshnessPolicyNotEvaluated />
  );
};

const FreshnessPolicyNotEvaluated = () => {
  return (
    <Popover
      interactionKind="hover"
      placement="top"
      content={
        <Box padding={{vertical: 12, horizontal: 16}} style={{width: '300px'}}>
          <Text size={12}>
            Freshness policies are a new feature under active development and are not evaluated by
            default. See{' '}
            <a
              href="https://docs.dagster.io/guides/labs/freshness"
              target="_blank"
              rel="noreferrer"
            >
              freshness policy documentation
            </a>{' '}
            to learn more.
          </Text>
        </Box>
      }
    >
      <Tag intent="none" icon="no_access">
        Not evaluated
      </Tag>
    </Popover>
  );
};

const QueryfulFreshnessPolicySection = ({assetKey, policy}: FreshnessPolicySectionProps) => {
  const {data, loading} = useQuery<FreshnessStatusQuery, FreshnessStatusQueryVariables>(
    FRESHNESS_STATUS_QUERY,
    {
      variables: {assetKey: {path: assetKey.path}},
    },
  );

  if (loading && !data) {
    return <Skeleton $width="100%" $height={24} />;
  }

  const assetNode = data?.assetNodeOrError;
  if (!assetNode || assetNode.__typename !== 'AssetNode') {
    return null;
  }

  const freshnessStatus = assetNode.freshnessStatusInfo?.freshnessStatus;
  const metadata = assetNode.freshnessStatusInfo?.freshnessStatusMetadata;
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
          <Text size={12} color="textLight">
            Last materialized <TimeFromNow unixTimestamp={lastMaterializedTimestamp} />
          </Text>
        ) : (
          <Text size={12} color="textLight">
            No materializations
          </Text>
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
  const {data, loading} = useQuery<FreshnessStatusQuery, FreshnessStatusQueryVariables>(
    FRESHNESS_STATUS_QUERY,
    {
      variables: {assetKey: {path: assetKey.path}},
    },
  );

  if (loading && !data) {
    return <Skeleton $width="100%" $height={24} />;
  }

  const assetNode = data?.assetNodeOrError;
  if (!assetNode || assetNode.__typename !== 'AssetNode') {
    return (
      <Tag intent="none" icon="no_access">
        Not found
      </Tag>
    );
  }

  const freshnessStatus = assetNode.freshnessStatusInfo?.freshnessStatus;
  const metadata = assetNode.freshnessStatusInfo?.freshnessStatusMetadata;
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
                <Text size={12}>
                  Last materialized <TimeFromNow unixTimestamp={lastMaterializedTimestamp} />
                </Text>
              ) : (
                <Text size={12}>No materializations</Text>
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
    <Text size={12} color="textLight">
      Fails if more than {dayjs.duration(policy.failWindowSeconds, 'seconds').humanize()} since last
      materialization
    </Text>
    {policy.warnWindowSeconds && (
      <Text size={12} color="textLight">
        Warns if more than {dayjs.duration(policy.warnWindowSeconds, 'seconds').humanize()} since
        last materialization
      </Text>
    )}
  </>
);

const CronFreshnessPolicyDetails = ({policy}: {policy: CronFreshnessPolicy}) => {
  const humanReadableDeadlineCron = humanCronString(policy.deadlineCron, {
    longTimezoneName: policy.timezone,
  });
  const humanReadableLowerBoundDelta = dayjs
    .duration(policy.lowerBoundDeltaSeconds, 'seconds')
    .humanize();

  return (
    <>
      <Text size={12} color="textLight">
        Deadline: {humanReadableDeadlineCron}
      </Text>
      <Text size={12} color="textLight">
        Fresh if materialized no earlier than {humanReadableLowerBoundDelta} before each deadline.
      </Text>
    </>
  );
};
