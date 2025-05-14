import {Box, ButtonLink, Colors, Icon, Tag, Tooltip} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

import {
  AssetDescription,
  AssetInsetForHoverEffect,
  AssetNameRow,
  AssetNodeBox,
  AssetNodeContainer,
  AssetNodeRowBox,
} from './AssetNode';
import {AssetNodeFacet, labelForFacet} from './AssetNodeFacets';
import {AssetNodeFreshnessRow, AssetNodeFreshnessRowOld} from './AssetNodeFreshnessRow';
import {AssetNodeHealthRow} from './AssetNodeHealthRow';
import {assetNodeLatestEventContent, buildAssetNodeStatusContent} from './AssetNodeStatusContent';
import {LiveDataForNode, LiveDataForNodeWithStaleData} from './Utils';
import {ASSET_NODE_TAGS_HEIGHT} from './layout';
import {featureEnabled} from '../app/Flags';
import {useAssetAutomationData} from '../asset-data/AssetAutomationDataProvider';
import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {AssetAutomationFragment} from '../asset-data/types/AssetAutomationDataProvider.types';
import {EvaluationUserLabel} from '../assets/AutoMaterializePolicyPage/EvaluationConditionalLabel';
import {ChangedReasonsTag} from '../assets/ChangedReasons';
import {StaleReasonsTag} from '../assets/Stale';
import {AssetChecksStatusSummary} from '../assets/asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKind} from '../graph/KindTags';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';
import {AssetNodeFragment} from './types/AssetNode.types';
import {EvaluationDetailDialog} from '../assets/AutoMaterializePolicyPage/EvaluationDetailDialog';

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
    <AssetInsetForHoverEffect>
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
          {facets.has(AssetNodeFacet.Freshness) &&
            (featureEnabled(FeatureFlag.flagUseNewObserveUIs) ? (
              <AssetNodeFreshnessRow definition={definition} liveData={liveData} />
            ) : (
              <AssetNodeFreshnessRowOld liveData={liveData} />
            ))}
          {facets.has(AssetNodeFacet.Automation) && (
            <AssetNodeAutomationRow definition={definition} automationData={automationData} />
          )}
          {facets.has(AssetNodeFacet.Status) &&
            (featureEnabled(FeatureFlag.flagUseNewObserveUIs) ? (
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
    </AssetInsetForHoverEffect>
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
            userLabel={automationData.automationCondition!.label!}
            expandedLabel={automationData.automationCondition!.expandedLabel}
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
    const owner = owners[0]!;
    return owner.__typename === 'UserAssetOwner' ? (
      <UserDisplayWrapNoPadding>
        <UserDisplay email={owner.email} size="very-small" />
      </UserDisplayWrapNoPadding>
    ) : (
      <Tag icon="people">{owner.team}</Tag>
    );
  }

  return (
    <Tooltip
      placement="top"
      content={
        <Box flex={{wrap: 'wrap', gap: 12}} style={{maxWidth: 300}}>
          {owners.map((o, idx) =>
            o.__typename === 'UserAssetOwner' ? (
              <UserDisplayWrapNoPadding key={idx}>
                <UserDisplay email={o.email} size="very-small" />
              </UserDisplayWrapNoPadding>
            ) : (
              <Tag key={idx} icon="people">
                {o.team}
              </Tag>
            ),
          )}
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

const UserDisplayWrapNoPadding = styled.div`
  & > div > div {
    background: none;
    padding: 0;
  }
`;
