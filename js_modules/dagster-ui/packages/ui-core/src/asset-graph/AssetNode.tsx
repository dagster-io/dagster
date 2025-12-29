import {Box, ButtonLink, Colors, FontFamily, Icon, Tag, Tooltip} from '@dagster-io/ui-components';
import clsx from 'clsx';
import isEqual from 'lodash/isEqual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import {assetHealthEnabled} from 'shared/app/assetHealthEnabled.oss';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled, {CSSObject} from 'styled-components';

import {gql} from '../apollo-client';
import {labelForFacet} from './AssetNodeFacets';
import {AssetNodeFacet} from './AssetNodeFacetsUtil';
import {AssetNodeFreshnessRow, AssetNodeFreshnessRowOld} from './AssetNodeFreshnessRow';
import {AssetNodeHealthRow} from './AssetNodeHealthRow';
import {AssetNodeMenuProps, useAssetNodeMenu} from './AssetNodeMenu';
import {assetNodeLatestEventContent, buildAssetNodeStatusContent} from './AssetNodeStatusContent';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {LiveDataForNode, LiveDataForNodeWithStaleData} from './Utils';
import {withMiddleTruncation} from '../app/Util';
import {useAssetAutomationData} from '../asset-data/AssetAutomationDataProvider';
import {useAssetHealthData} from '../asset-data/AssetHealthDataProvider';
import {useAssetLiveData} from '../asset-data/AssetLiveDataProvider';
import {AssetAutomationFragment} from '../asset-data/types/AssetAutomationDataProvider.types';
import {statusToIconAndColor} from '../assets/AssetHealthSummary';
import {EvaluationUserLabel} from '../assets/AutoMaterializePolicyPage/EvaluationConditionalLabel';
import {EvaluationDetailDialog} from '../assets/AutoMaterializePolicyPage/EvaluationDetailDialog';
import {ChangedReasonsTag, MinimalNodeChangedDot} from '../assets/ChangedReasons';
import {MinimalNodeStaleDot, StaleReasonsTag, isAssetStale} from '../assets/Stale';
import {AssetChecksStatusSummary} from '../assets/asset-checks/AssetChecksStatusSummary';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetKind} from '../graph/KindTags';
import {compactNumber} from '../ui/formatters';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';
import styles from './css/AssetNode.module.css';
import {ASSET_NODE_NAME_MAX_LENGTH, ASSET_NODE_TAGS_HEIGHT} from './layout';
import {AssetNodeFragment} from './types/AssetNode.types';

interface Props2025 {
  definition: AssetNodeFragment;
  selected: boolean;
  facets: Set<AssetNodeFacet>;
  onChangeAssetSelection?: (selection: string) => void;
}

export const ASSET_NODE_HOVER_EXPAND_HEIGHT = 3;

export const AssetNode = React.memo((props: Props2025) => {
  const {liveData} = useAssetLiveData(props.definition.assetKey);
  return (
    <AssetNodeWithLiveData
      {...props}
      liveData={liveData}
      assetHealthEnabled={assetHealthEnabled()}
    />
  );
}, isEqual);

export const AssetNodeWithLiveData = ({
  definition,
  selected,
  facets,
  onChangeAssetSelection,
  liveData,
  automationData,
  assetHealthEnabled,
}: Props2025 & {liveData: LiveDataForNodeWithStaleData | undefined} & {
  automationData?: AssetAutomationFragment | undefined;
  assetHealthEnabled: boolean;
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
          (assetHealthEnabled ? (
            <AssetNodeFreshnessRow definition={definition} liveData={liveData} />
          ) : (
            <AssetNodeFreshnessRowOld liveData={liveData} />
          ))}
        {facets.has(AssetNodeFacet.Automation) && (
          <AssetNodeAutomationRow definition={definition} automationData={automationData} />
        )}
        {facets.has(AssetNodeFacet.Status) &&
          (assetHealthEnabled ? (
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

export const AssetNameRow = ({definition}: {definition: AssetNodeFragment}) => {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1]!;

  return (
    <AssetName $isMaterializable={definition.isMaterializable}>
      <span style={{marginTop: 1}}>
        <Icon name={definition.isMaterializable ? 'asset' : 'source_asset'} />
      </span>
      <div
        data-tooltip={displayName}
        data-tooltip-style={definition.isMaterializable ? NameTooltipStyle : NameTooltipStyleSource}
        style={{overflow: 'hidden', textOverflow: 'ellipsis'}}
      >
        {withMiddleTruncation(displayName, {
          maxLength: ASSET_NODE_NAME_MAX_LENGTH,
        })}
      </div>
      <div style={{flex: 1}} />
    </AssetName>
  );
};

export const AssetNodeRowBox = styled(Box)`
  white-space: nowrap;
  line-height: 12px;
  font-size: 12px;
  height: 24px;
  a:hover {
    text-decoration: none;
  }
  &:last-child {
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
  }
`;

export const AssetNodeContextMenuWrapper = React.memo(
  ({children, ...menuProps}: AssetNodeMenuProps & {children: React.ReactNode}) => {
    const {dialog, menu} = useAssetNodeMenu(menuProps);
    return (
      <>
        <ContextMenuWrapper menu={menu} stopPropagation>
          {children}
        </ContextMenuWrapper>
        {dialog}
      </>
    );
  },
);

type AssetNodeMinimalProps = {
  selected: boolean;
  definition: AssetNodeFragment;
  facets: Set<AssetNodeFacet> | null;
  height: number;
};

export const AssetNodeMinimal = (props: AssetNodeMinimalProps) => {
  return assetHealthEnabled() ? (
    <AssetNodeMinimalWithHealth {...props} />
  ) : (
    <AssetNodeMinimalWithoutHealth {...props} />
  );
};

export const AssetNodeMinimalWithHealth = ({
  definition,
  facets,
  height,
  selected,
}: AssetNodeMinimalProps) => {
  const {isMaterializable, assetKey} = definition;
  const {liveData} = useAssetLiveData(assetKey);
  const {liveData: healthData} = useAssetHealthData(assetKey);
  const health = healthData?.assetHealth;

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const displayName = assetKey.path[assetKey.path.length - 1]!;
  const isChanged = definition.changedReasons.length;
  const isStale = isAssetStale(liveData);

  const queuedRuns = liveData?.unstartedRunIds.length;
  const inProgressRuns = liveData?.inProgressRunIds.length;
  const numMaterializing = liveData?.partitionStats?.numMaterializing;
  const isMaterializing = numMaterializing || inProgressRuns || queuedRuns;

  const {borderColor, backgroundColor} = React.useMemo(() => {
    if (isMaterializing) {
      return {backgroundColor: Colors.backgroundBlue(), borderColor: Colors.accentBlue()};
    }
    return statusToIconAndColor[health?.assetHealth ?? 'undefined'];
  }, [health, isMaterializing]);

  // old design
  let paddingTop = height / 2 - 52;
  let nodeHeight = 86;

  if (facets !== null) {
    const topTagsPresent = facets.has(AssetNodeFacet.UnsyncedTag);
    const bottomTagsPresent = facets.has(AssetNodeFacet.KindTag);
    paddingTop = ASSET_NODE_VERTICAL_MARGIN + (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);
    nodeHeight =
      height -
      ASSET_NODE_VERTICAL_MARGIN * 2 -
      (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : ASSET_NODE_HOVER_EXPAND_HEIGHT) -
      (bottomTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);

    // Ensure that we have room for the label, even if it makes the minimal format larger.
    if (nodeHeight < 38) {
      nodeHeight = 38;
    }
  }

  return (
    <MinimalAssetNodeContainer $selected={selected} style={{paddingTop}}>
      <TooltipStyled
        content={displayName}
        canShow={displayName.length > 14}
        targetTagName="div"
        position="top"
      >
        <MinimalAssetNodeBox
          $selected={selected}
          $isMaterializable={isMaterializable}
          $background={backgroundColor}
          $border={borderColor}
          $inProgress={!!inProgressRuns}
          $isQueued={!!queuedRuns}
          $height={nodeHeight}
        >
          {isChanged ? (
            <MinimalNodeChangedDot changedReasons={definition.changedReasons} assetKey={assetKey} />
          ) : null}
          {isStale ? <MinimalNodeStaleDot assetKey={assetKey} liveData={liveData} /> : null}
          <MinimalName style={{fontSize: 24}} $isMaterializable={isMaterializable}>
            {withMiddleTruncation(displayName, {maxLength: 18})}
          </MinimalName>
        </MinimalAssetNodeBox>
      </TooltipStyled>
    </MinimalAssetNodeContainer>
  );
};

export const AssetNodeMinimalWithoutHealth = ({
  definition,
  facets,
  height,
  selected,
}: AssetNodeMinimalProps) => {
  const {isMaterializable, assetKey} = definition;
  const {liveData} = useAssetLiveData(assetKey);

  const {border, background} = buildAssetNodeStatusContent({assetKey, definition, liveData});
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const displayName = assetKey.path[assetKey.path.length - 1]!;

  const isChanged = definition.changedReasons.length;
  const isStale = isAssetStale(liveData);

  const queuedRuns = liveData?.unstartedRunIds.length;
  const inProgressRuns = liveData?.inProgressRunIds.length;

  // old design
  let paddingTop = height / 2 - 52;
  let nodeHeight = 86;

  if (facets !== null) {
    const topTagsPresent = facets.has(AssetNodeFacet.UnsyncedTag);
    const bottomTagsPresent = facets.has(AssetNodeFacet.KindTag);
    paddingTop = ASSET_NODE_VERTICAL_MARGIN + (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);
    nodeHeight =
      height -
      ASSET_NODE_VERTICAL_MARGIN * 2 -
      (topTagsPresent ? ASSET_NODE_TAGS_HEIGHT : ASSET_NODE_HOVER_EXPAND_HEIGHT) -
      (bottomTagsPresent ? ASSET_NODE_TAGS_HEIGHT : 0);

    // Ensure that we have room for the label, even if it makes the minimal format larger.
    if (nodeHeight < 38) {
      nodeHeight = 38;
    }
  }

  return (
    <MinimalAssetNodeContainer $selected={selected} style={{paddingTop}}>
      <TooltipStyled
        content={displayName}
        canShow={displayName.length > 14}
        targetTagName="div"
        position="top"
      >
        <MinimalAssetNodeBox
          $selected={selected}
          $isMaterializable={isMaterializable}
          $background={background}
          $border={border}
          $inProgress={!!inProgressRuns}
          $isQueued={!!queuedRuns}
          $height={nodeHeight}
        >
          {isChanged ? (
            <MinimalNodeChangedDot changedReasons={definition.changedReasons} assetKey={assetKey} />
          ) : null}
          {isStale ? <MinimalNodeStaleDot assetKey={assetKey} liveData={liveData} /> : null}
          <MinimalName style={{fontSize: 24}} $isMaterializable={isMaterializable}>
            {withMiddleTruncation(displayName, {maxLength: 18})}
          </MinimalName>
        </MinimalAssetNodeBox>
      </TooltipStyled>
    </MinimalAssetNodeContainer>
  );
};

// Note: This fragment should only contain fields that are needed for
// useAssetGraphData and the Asset DAG. Some pages of Dagster UI request this
// fragment for every AssetNode on the instance. Add fields with care!
//
export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    graphName
    hasMaterializePermission
    jobNames
    changedReasons
    opNames
    opVersion
    description
    computeKind
    isPartitioned
    isObservable
    isMaterializable
    isAutoCreatedStub
    owners {
      ... on TeamAssetOwner {
        team
      }
      ... on UserAssetOwner {
        email
      }
    }
    assetKey {
      ...AssetNodeKey
    }
    tags {
      key
      value
    }
    kinds
  }

  fragment AssetNodeKey on AssetKey {
    path
  }
`;

export const ASSET_NODE_VERTICAL_MARGIN = 6;

export const AssetNodeContainer = styled.div<{$selected: boolean}>`
  user-select: none;
  cursor: pointer;

  & *:focus {
    outline: 0;
  }
`;

const AssetNodeShowOnHover = styled.span`
  display: none;
`;

export const AssetNodeBox = styled.div<{
  $isMaterializable: boolean;
  $selected: boolean;
  $noScale?: boolean;
}>`
  ${(p) =>
    !p.$isMaterializable
      ? `border: 2px dashed ${p.$selected ? Colors.accentGrayHover() : Colors.accentGray()}`
      : `border: 2px solid ${
          p.$selected ? Colors.lineageNodeBorderSelected() : Colors.lineageNodeBorder()
        }`};
  ${(p) => p.$selected && `outline: 2px solid ${Colors.lineageNodeBorderSelected()}`};

  background: ${Colors.backgroundDefault()};
  border-radius: 10px;
  position: relative;
  margin: ${ASSET_NODE_VERTICAL_MARGIN}px 0;
  transition: all 150ms linear;
  &:hover {
    ${(p) => !p.$selected && `border: 2px solid ${Colors.lineageNodeBorderHover()};`};
    box-shadow: ${Colors.shadowDefault()} 0px 1px 4px 0px;
    scale: ${(p) => (p.$noScale ? '1' : '1.03')};
    ${AssetNodeShowOnHover} {
      display: initial;
    }
  }
`;

/** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
const NameCSS: CSSObject = {
  padding: '3px 0 3px 6px',
  color: Colors.textDefault(),
  fontSize: 14,
  fontFamily: FontFamily.monospace,
  fontWeight: 600,
};

export const NameTooltipCSS: CSSObject = {
  ...NameCSS,
  top: -9,
  left: -12,
  fontSize: 14,
};

export const NameTooltipStyle = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.lineageNodeBackground(),
  border: `none`,
});

const NameTooltipStyleSource = JSON.stringify({
  ...NameTooltipCSS,
  background: Colors.backgroundLight(),
  border: `none`,
});

const AssetName = styled.div<{$isMaterializable: boolean}>`
  ${NameCSS};
  display: flex;
  gap: 4px;
  background: ${(p) =>
    p.$isMaterializable ? Colors.lineageNodeBackground() : Colors.backgroundLight()};
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  height: 100%;
`;

const MinimalAssetNodeBox = styled.div<{
  $isMaterializable: boolean;
  $selected: boolean;
  $background: string;
  $border: string;
  $inProgress: boolean;
  $isQueued: boolean;
  $height: number;
}>`
  background: ${(p) => p.$background};
  overflow: hidden;
  ${(p) =>
    !p.$isMaterializable
      ? `border: 4px dashed ${p.$selected ? Colors.accentGray() : p.$border}`
      : `border: 4px solid ${p.$selected ? Colors.lineageNodeBorderSelected() : p.$border}`};
  ${(p) =>
    p.$inProgress
      ? `
      background-color: ${p.$background};
      &::after {
        inset: 0;
        position: absolute;
        transform: translateX(-100%);
        mask-image: linear-gradient(90deg, rgba(255,255,255,0) 0, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3));
        background: ${p.$background};
        animation: shimmer 1.5s infinite;
        content: '';
      }

      @keyframes shimmer {
        100% {
          transform: translateX(100%);
        }
      }
  `
      : ''}

  ${(p) =>
    p.$isQueued
      ? `
      border: none;
      &::after {
        inset: 0;
        position: absolute;
        animation: pulse 0.75s infinite alternate;
        border-radius: 16px;
        border: 4px solid ${p.$border};
        content: '';
      }
      @keyframes pulse {
        0% {
          opacity: 0.2;
        }
        100% {
          opacity: 1;
        }
      }
      `
      : ''}
  border-radius: 16px;
  position: relative;
  padding: 2px;
  height: ${(p) => p.$height}px;
  &:hover {
    box-shadow: ${Colors.shadowDefault()} 0px 2px 12px 0px;
  }
`;

const MinimalName = styled(AssetName)`
  font-weight: 600;
  white-space: nowrap;
  position: absolute;
  background: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
`;

export const AssetDescription = styled.div<{$color: string}>`
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: ${(p) => p.$color};
  font-size: 12px;
`;

const TooltipStyled = styled(Tooltip)`
  height: 100%;
`;
