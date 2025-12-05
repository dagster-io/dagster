import {Box, ButtonLink, Colors, Icon, Tag, Tooltip} from '@dagster-io/ui-components';
import clsx from 'clsx';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import {observeEnabled} from 'shared/app/observeEnabled.oss';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';

import {
  AssetDescription,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
  AssetNodeRowBox,
} from './AssetNode';
import {labelForFacet} from './AssetNodeFacets';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {AssetNodeFreshnessRow, AssetNodeFreshnessRowOld} from './AssetNodeFreshnessRow';
import {AssetNodeHealthRow} from './AssetNodeHealthRow';
import {assetNodeLatestEventContent, buildAssetNodeStatusContent} from './AssetNodeStatusContent';
import {LiveDataForNode, LiveDataForNodeWithStaleData} from './Utils';
import styles from './css/AssetNode2025.module.css';
import {ASSET_NODE_TAGS_HEIGHT} from './layout';
import {useAssetAutomationData} from '../asset-data/AssetAutomationDataProvider';
import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {AssetAutomationFragment} from '../asset-data/types/AssetAutomationDataProvider.types';
import {EvaluationUserLabel} from '../assets/AutoMaterializePolicyPage/EvaluationConditionalLabel';
import {EvaluationDetailDialog} from '../assets/AutoMaterializePolicyPage/EvaluationDetailDialog';
import {ChangedReasonsTag} from '../assets/ChangedReasons';
import {StaleReasonsTag} from '../assets/Stale';
import {AssetChecksStatusSummary} from '../assets/asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKind} from '../graph/KindTags';
import {compactNumber} from '../ui/formatters';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';
import {AssetNodeFragment} from './types/AssetNode.types';

interface Props2025 {
  definition: AssetNodeFragment;
  selected: boolean;
  facets: Set<AssetNodeFacet>;
  onChangeAssetSelection?: (selection: string) => void;
}

export const ASSET_NODE_HOVER_EXPAND_HEIGHT = 3;

export const AssetNode2025 = React.memo((props: Props2025) => {
  const {liveData} = useAssetLiveData(props.definition.assetKey);
  return <AssetNodeWithLiveData {...props} liveData={liveData} />;
}, isEqual);

export const AssetNodeWithLiveData = ({
  definition,
  selected,
  facets,
  onChangeAssetSelection,
  liveData,
  automationData,
}: Props2025 & {liveData: LiveDataForNodeWithStaleData | undefined} & {
  automationData?: AssetAutomationFragment | undefined;
}) => {
  return (
    <AssetNodeContainer $selected={selected}>
      {facets.has(AssetNodeFacet.UnsyncedTag) ? (
        <Box
          flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}
          style={{minHeight: ASSET_NODE_TAGS_HEIGHT}}
        >
          <div>
            <StaleReasonsTag liveData={liveData} assetKey={definition.assetKey} />
          </div>
          <ChangedReasonsTag
            changedReasons={definition.changedReasons}
            assetKey={definition.assetKey}
          />
        </Box>
      ) : (
        <div style={{minHeight: ASSET_NODE_HOVER_EXPAND_HEIGHT}} />
      )}
      <AssetNodeBox $selected={selected} $isMaterializable={definition.isMaterializable}>
        <AssetNameRow definition={definition} />
        {facets.has(AssetNodeFacet.Description) && (
          <AssetNodeRow label={null}>
            {definition.description ? (
              <AssetDescription $color={Colors.textDefault()}>
                {markdownToPlaintext(definition.description).split('\n')[0]}
              </AssetDescription>
            ) : (
              <AssetDescription $color={Colors.textDefault()}>No description</AssetDescription>
            )}
          </AssetNodeRow>
        )}
        {facets.has(AssetNodeFacet.Owner) && (
          <AssetNodeRow label={labelForFacet(AssetNodeFacet.Owner)}>
            {definition.owners.length > 0 ? (
              <SingleOwnerOrTooltip owners={definition.owners} />
            ) : null}
          </AssetNodeRow>
        )}
        {facets.has(AssetNodeFacet.LatestEvent) && (
          <AssetNodeRow label={labelForFacet(AssetNodeFacet.LatestEvent)}>
            {assetNodeLatestEventContent({definition, liveData})}
          </AssetNodeRow>
        )}
        {facets.has(AssetNodeFacet.Checks) && (
          <AssetNodeRow label={labelForFacet(AssetNodeFacet.Checks)}>
            {liveData && liveData.assetChecks.length > 0 ? (
              <Link
                to={assetDetailsPathForKey(definition.assetKey, {view: 'checks'})}
                onClick={(e) => e.stopPropagation()}
              >
                <AssetChecksStatusSummary
                  liveData={liveData}
                  rendering="dag2025"
                  assetKey={definition.assetKey}
                />
              </Link>
            ) : null}
          </AssetNodeRow>
        )}
        {facets.has(AssetNodeFacet.Partitions) && (
          <AssetNodeRow label={labelForFacet(AssetNodeFacet.Partitions)}>
            <PartitionsFacetContent definition={definition} liveData={liveData} />
          </AssetNodeRow>
        )}
        {facets.has(AssetNodeFacet.Freshness) &&
          (observeEnabled() ? (
            <AssetNodeFreshnessRow definition={definition} liveData={liveData} />
          ) : (
            <AssetNodeFreshnessRowOld liveData={liveData} />
          ))}
        {facets.has(AssetNodeFacet.Automation) && (
          <AssetNodeAutomationRow definition={definition} automationData={automationData} />
        )}
        {facets.has(AssetNodeFacet.Status) &&
          (observeEnabled() ? (
            <AssetNodeHealthRow definition={definition} liveData={liveData} />
          ) : (
            <AssetNodeStatusRow definition={definition} liveData={liveData} />
          ))}
      </AssetNodeBox>
      {facets.has(AssetNodeFacet.KindTag) && (
        <Box
          style={{minHeight: ASSET_NODE_TAGS_HEIGHT}}
          flex={{alignItems: 'center', direction: 'row-reverse', gap: 8}}
        >
          {definition.kinds.map((kind) => (
            <AssetKind
              key={kind}
              kind={kind}
              style={{position: 'relative', margin: 0}}
              onChangeAssetSelection={onChangeAssetSelection}
            />
          ))}
        </Box>
      )}
    </AssetNodeContainer>
  );
};

export const AssetNodeAutomationRow = ({
  definition,
  automationData,
}: {
  definition: AssetNodeFragment;
  automationData?: AssetAutomationFragment;
}) => {
  return automationData ? (
    <AssetNodeAutomationRowWithData definition={definition} automationData={automationData} />
  ) : (
    <AssetNodeAutomationRowWithoutData definition={definition} />
  );
};

const AssetNodeAutomationRowWithoutData = ({definition}: {definition: AssetNodeFragment}) => {
  const {liveData: liveAutomationData} = useAssetAutomationData(definition.assetKey, 'asset-graph');
  return (
    <AssetNodeAutomationRowWithData definition={definition} automationData={liveAutomationData} />
  );
};

export const AssetNodeAutomationRowWithData = ({
  definition,
  automationData,
}: {
  definition: AssetNodeFragment;
  automationData: AssetAutomationFragment | undefined;
}) => {
  const hasAutomationCondition = !!automationData?.automationCondition;
  const sensors = automationData?.targetingInstigators.filter(
    (instigator) => instigator.__typename === 'Sensor',
  );
  const hasSensors = !!sensors?.length;
  const sensorsEnabled = !!sensors?.some((sensor) => sensor.sensorState.status === 'RUNNING');
  const firstSensor = hasSensors ? sensors[0] : null;
  const schedules = automationData?.targetingInstigators.filter(
    (instigator) => instigator.__typename === 'Schedule',
  );
  const hasSchedules = !!schedules?.length;
  const firstSchedule = hasSchedules ? schedules[0] : null;
  const schedulesEnabled = schedules?.some(
    (schedule) => schedule.scheduleState.status === 'RUNNING',
  );
  const automationSensors = sensors?.filter((sensor) => sensor.sensorType === 'AUTOMATION');
  const automationSensorsEnabled = automationSensors?.some(
    (sensor) => sensor.sensorState.status === 'RUNNING',
  );

  const content = () => {
    if (hasAutomationCondition && !hasSchedules && !hasSensors) {
      return (
        <AutomationConditionEvaluationLink definition={definition} automationData={automationData}>
          <EvaluationUserLabel
            userLabel={automationData.automationCondition?.label ?? 'condition'}
            expandedLabel={automationData.automationCondition?.expandedLabel ?? []}
            small
          />
        </AutomationConditionEvaluationLink>
      );
    }

    if (!hasAutomationCondition && !hasSensors && !hasSchedules) {
      return null;
    }

    return (
      <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
        {firstSensor ? (
          <Tooltip
            content={sensors?.length === 1 ? firstSensor.name : 'Multiple sensors'}
            placement="top"
          >
            <Icon
              name="sensor"
              color={sensorsEnabled ? Colors.accentGreen() : Colors.textLight()}
            />
          </Tooltip>
        ) : null}
        {firstSchedule ? (
          <Tooltip
            content={schedules?.length === 1 ? firstSchedule.name : 'Multiple schedules'}
            placement="top"
          >
            <Icon
              name="schedule"
              color={schedulesEnabled ? Colors.accentGreen() : Colors.textLight()}
            />
          </Tooltip>
        ) : null}
        {hasAutomationCondition ? (
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          <Tooltip content={automationData.automationCondition!.label!} placement="top">
            <AutomationConditionEvaluationLink
              definition={definition}
              automationData={automationData}
            >
              <Icon
                name="automation"
                color={automationSensorsEnabled ? Colors.accentGreen() : Colors.textLight()}
              />
            </AutomationConditionEvaluationLink>
          </Tooltip>
        ) : null}
      </Box>
    );
  };

  return <AssetNodeRow label={labelForFacet(AssetNodeFacet.Automation)}>{content()}</AssetNodeRow>;
};

const PartitionsFacetContent = ({
  definition,
  liveData,
}: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  // If asset is not partitioned, show "Not partitioned"
  if (!definition.isPartitioned) {
    return <span style={{color: Colors.textLighter()}}>–</span>;
  }

  const partitionStats = liveData?.partitionStats;
  if (!partitionStats || partitionStats.numPartitions === 0) {
    return null;
  }

  const {numMaterialized, numPartitions, numFailed} = partitionStats;
  const filledPct = Math.round((numMaterialized / numPartitions) * 100);
  const displayText =
    numFailed > 0
      ? `${filledPct}% filled (${compactNumber(numFailed)} failed)`
      : `${filledPct}% filled`;

  return (
    <Link
      to={assetDetailsPathForKey(definition.assetKey, {view: 'partitions'})}
      onClick={(e) => e.stopPropagation()}
    >
      {displayText}
    </Link>
  );
};

export const AssetNodeRow = ({
  label,
  children,
}: {
  label: string | null;
  children: React.ReactNode | null;
}) => {
  return (
    <AssetNodeRowBox
      padding={{horizontal: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
      border="bottom"
    >
      {label ? <span style={{color: Colors.textLight()}}>{label}</span> : undefined}
      {children ? children : <span style={{color: Colors.textLighter()}}>–</span>}
    </AssetNodeRowBox>
  );
};

const AssetNodeStatusRow = ({
  definition,
  liveData,
}: {
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
}) => {
  const {content, background} = buildAssetNodeStatusContent({
    assetKey: definition.assetKey,
    definition,
    liveData,
  });
  return (
    <AssetNodeRowBox
      background={background}
      padding={{horizontal: 8}}
      flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
    >
      {content}
    </AssetNodeRowBox>
  );
};

const SingleOwnerOrTooltip = ({owners}: {owners: AssetNodeFragment['owners']}) => {
  if (owners.length === 1) {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const owner = owners[0]!;
    return (
      <div className={styles.UserDisplayWrapNoPadding}>
        {owner.__typename === 'UserAssetOwner' ? (
          <UserDisplay email={owner.email} size="very-small" />
        ) : (
          <Tag icon="people">{owner.team}</Tag>
        )}
      </div>
    );
  }

  return (
    <Tooltip
      placement="top"
      content={
        <Box flex={{wrap: 'wrap', gap: 12}} style={{maxWidth: 300, lineHeight: 0}}>
          {owners.map((o, idx) => (
            <div
              key={idx}
              className={clsx(styles.UserDisplayWrapNoPadding, styles.UserDisplayInTooltip)}
            >
              {o.__typename === 'UserAssetOwner' ? (
                <UserDisplay email={o.email} size="very-small" />
              ) : (
                <Tag icon="people">{o.team}</Tag>
              )}
            </div>
          ))}
        </Box>
      }
    >
      {`${owners.length} owners`}
    </Tooltip>
  );
};

export const AutomationConditionEvaluationLink = ({
  definition,
  automationData,
  children,
}: {
  definition: AssetNodeFragment;
  automationData?: AssetAutomationFragment;
  children: React.ReactNode;
}) => {
  const [isOpen, setOpen] = React.useState(false);
  if (automationData?.lastAutoMaterializationEvaluationRecord) {
    return (
      <>
        <ButtonLink
          onClick={(e) => {
            e.stopPropagation();
            setOpen(true);
          }}
        >
          {children}
        </ButtonLink>
        <EvaluationDetailDialog
          isOpen={isOpen}
          onClose={() => setOpen(false)}
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          evaluationID={automationData.lastAutoMaterializationEvaluationRecord!.evaluationId}
          assetKeyPath={definition.assetKey.path}
        />
      </>
    );
  }

  return (
    <Link
      to={assetDetailsPathForKey(definition.assetKey, {view: 'automation'})}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </Link>
  );
};
