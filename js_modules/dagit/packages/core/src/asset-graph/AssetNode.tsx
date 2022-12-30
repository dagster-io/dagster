import {gql} from '@apollo/client';
import {Colors, Icon, FontFamily, Box, CaptionMono, Caption, Spinner} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import React from 'react';
import styled from 'styled-components/macro';

import {withMiddleTruncation} from '../app/Util';
import {humanizedLateString, isAssetLate} from '../assets/CurrentMinutesLateTag';
import {isAssetStale} from '../assets/StaleTag';
import {OpTags} from '../graph/OpTags';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';

import {AssetLatestRunSpinner, AssetRunLink} from './AssetRunLinking';
import {LiveDataForNode} from './Utils';
import {ASSET_NODE_NAME_MAX_LENGTH} from './layout';
import {AssetNodeFragment} from './types/AssetNodeFragment';

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  selected: boolean;
}> = React.memo(({definition, selected, liveData}) => {
  const firstOp = definition.opNames.length ? definition.opNames[0] : null;

  // Used for linking to the run with this step highlighted. We only support highlighting
  // a single step, so just use the first one.
  const stepKey = firstOp || '';

  const displayName = definition.assetKey.path[definition.assetKey.path.length - 1];
  const isSource = definition.isSource;

  return (
    <AssetInsetForHoverEffect>
      <AssetNodeContainer $selected={selected}>
        <AssetNodeBox $selected={selected} $isSource={isSource}>
          <Name $isSource={isSource}>
            <span style={{marginTop: 1}}>
              <Icon name={isSource ? 'source_asset' : 'asset'} />
            </span>
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>
              {withMiddleTruncation(displayName, {
                maxLength: ASSET_NODE_NAME_MAX_LENGTH,
              })}
            </div>
            <div style={{flex: 1}} />
          </Name>
          {definition.description ? (
            <Description $color={Colors.Gray800}>
              {markdownToPlaintext(definition.description).split('\n')[0]}
            </Description>
          ) : (
            <Description $color={Colors.Gray400}>No description</Description>
          )}
          {definition.isObservable && isSource ? (
            <Stats>
              <StatsRow>
                <span>Observed</span>
                {liveData?.lastObservation ? (
                  <CaptionMono style={{textAlign: 'right'}}>
                    <AssetRunLink
                      runId={liveData.lastObservation.runId}
                      event={{stepKey, timestamp: liveData.lastObservation.timestamp}}
                    >
                      <TimestampDisplay
                        timestamp={Number(liveData.lastObservation.timestamp) / 1000}
                        timeFormat={{showSeconds: false, showTimezone: false}}
                      />
                    </AssetRunLink>
                  </CaptionMono>
                ) : (
                  <span>–</span>
                )}
              </StatsRow>
            </Stats>
          ) : isSource ? null : (
            <AssetNodeStatusRow definition={definition} liveData={liveData} stepKey={stepKey} />
          )}
          {definition.computeKind && (
            <OpTags
              minified={false}
              style={{right: -2, paddingTop: 7}}
              tags={[
                {
                  label: definition.computeKind,
                  onClick: () => {
                    window.requestAnimationFrame(() =>
                      document.dispatchEvent(new Event('show-kind-info')),
                    );
                  },
                },
              ]}
            />
          )}
        </AssetNodeBox>
      </AssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
}, isEqual);

export const AssetNodeStatusBox: React.FC<{background: string}> = ({background, children}) => (
  <Box
    padding={{horizontal: 8}}
    style={{
      borderBottomLeftRadius: 6,
      borderBottomRightRadius: 6,
      whiteSpace: 'nowrap',
      lineHeight: 12,
      height: 24,
    }}
    flex={{justifyContent: 'space-between', alignItems: 'center', gap: 6}}
    background={background}
  >
    {children}
  </Box>
);

export const AssetNodeStatusRow: React.FC<{
  definition: AssetNodeFragment;
  liveData: LiveDataForNode | undefined;
  stepKey: string;
}> = ({definition, liveData, stepKey}) => {
  if (definition.isSource) {
    return <span />;
  }

  if (!liveData) {
    return (
      <AssetNodeStatusBox background={Colors.Gray100}>
        <Spinner purpose="caption-text" />
        <Caption style={{flex: 1}} color={Colors.Gray800}>
          Loading...
        </Caption>
      </AssetNodeStatusBox>
    );
  }

  const {
    lastMaterialization,
    runWhichFailedToMaterialize,
    inProgressRunIds,
    unstartedRunIds,
  } = liveData;

  const materializingRunId = inProgressRunIds[0] || unstartedRunIds[0];
  const late = isAssetLate(liveData);

  if (materializingRunId) {
    return (
      <AssetNodeStatusBox background={Colors.Blue50}>
        <AssetLatestRunSpinner liveData={liveData} />
        <Caption style={{flex: 1}} color={Colors.Gray800}>
          Materializing...
        </Caption>
        <AssetRunLink runId={materializingRunId} />
      </AssetNodeStatusBox>
    );
  }

  const lastMaterializationLink = lastMaterialization ? (
    <AssetRunLink
      runId={lastMaterialization.runId}
      event={{stepKey, timestamp: lastMaterialization.timestamp}}
    >
      <TimestampDisplay
        timestamp={Number(lastMaterialization.timestamp) / 1000}
        timeFormat={{showSeconds: false, showTimezone: false}}
      />
    </AssetRunLink>
  ) : undefined;

  if (runWhichFailedToMaterialize || late) {
    return (
      <AssetNodeStatusBox background={Colors.Red50}>
        <Caption color={Colors.Red700}>
          {runWhichFailedToMaterialize && late
            ? `Failed (Late)`
            : late
            ? humanizedLateString(liveData.freshnessInfo.currentMinutesLate)
            : 'Failed'}
        </Caption>
        {lastMaterializationLink}
      </AssetNodeStatusBox>
    );
  }

  if (!lastMaterialization) {
    return (
      <AssetNodeStatusBox background={Colors.Yellow50}>
        <Caption color={Colors.Yellow700}>Never materialized</Caption>
      </AssetNodeStatusBox>
    );
  }

  if (!liveData.freshnessPolicy && isAssetStale(liveData)) {
    return (
      <AssetNodeStatusBox background={Colors.Yellow50}>
        <Caption color={Colors.Yellow700}>Stale</Caption>
        {lastMaterializationLink}
      </AssetNodeStatusBox>
    );
  }

  return (
    <AssetNodeStatusBox background={Colors.Green50}>
      <Caption color={Colors.Green700}>Materialized</Caption>
      {lastMaterializationLink}
    </AssetNodeStatusBox>
  );
};

export const AssetNodeMinimal: React.FC<{
  selected: boolean;
  liveData?: LiveDataForNode;
  definition: AssetNodeFragment;
}> = ({selected, definition, liveData}) => {
  const {isSource, assetKey} = definition;
  const displayName = assetKey.path[assetKey.path.length - 1];
  const materializingRunId = liveData?.inProgressRunIds?.[0] || liveData?.unstartedRunIds?.[0];

  const [background, border] =
    !liveData || definition.isSource
      ? [Colors.Gray100, Colors.Gray300]
      : materializingRunId
      ? [Colors.Blue50, Colors.Blue500]
      : liveData?.runWhichFailedToMaterialize || isAssetLate(liveData)
      ? [Colors.Red50, Colors.Red500]
      : !liveData?.lastMaterialization || (!liveData.freshnessPolicy && isAssetStale(liveData))
      ? [Colors.Yellow50, Colors.Yellow500]
      : [Colors.Green50, Colors.Green500];

  return (
    <AssetInsetForHoverEffect>
      <MinimalAssetNodeContainer $selected={selected}>
        <MinimalAssetNodeBox
          $selected={selected}
          $isSource={isSource}
          $background={background}
          $border={border}
        >
          <div style={{position: 'absolute', bottom: 6, left: 6}}>
            <AssetLatestRunSpinner liveData={liveData} purpose="section" />
          </div>

          <MinimalName style={{fontSize: 30}} $isSource={isSource}>
            {withMiddleTruncation(displayName, {maxLength: 17})}
          </MinimalName>
        </MinimalAssetNodeBox>
      </MinimalAssetNodeContainer>
    </AssetInsetForHoverEffect>
  );
};

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opNames
    repository {
      id
    }
    assetKey {
      path
    }
    assetMaterializations(limit: 1) {
      ...AssetNodeLiveMaterialization
    }
    freshnessPolicy {
      ...AssetNodeLiveFreshnessPolicy
    }
    freshnessInfo {
      ...AssetNodeLiveFreshnessInfo
    }
    assetObservations(limit: 1) {
      ...AssetNodeLiveObservation
    }
    currentLogicalVersion
    projectedLogicalVersion
  }

  fragment AssetNodeLiveFreshnessPolicy on FreshnessPolicy {
    maximumLagMinutes
    cronSchedule
  }

  fragment AssetNodeLiveFreshnessInfo on AssetFreshnessInfo {
    currentMinutesLate
  }

  fragment AssetNodeLiveMaterialization on MaterializationEvent {
    timestamp
    runId
  }

  fragment AssetNodeLiveObservation on ObservationEvent {
    timestamp
    runId
  }
`;

// Note: This fragment should only contain fields that are needed for
// useAssetGraphData and the Asset DAG. Some pages of Dagit request this
// fragment for every AssetNode on the instance. Add fields with care!
//
export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    graphName
    jobNames
    opNames
    opVersion
    description
    computeKind
    isPartitioned
    isObservable
    isSource
    assetKey {
      ...AssetNodeKey
    }
  }

  fragment AssetNodeKey on AssetKey {
    path
  }
`;

const AssetInsetForHoverEffect = styled.div`
  padding: 10px 4px 2px 4px;
  height: 100%;
`;

export const AssetNodeContainer = styled.div<{$selected: boolean}>`
  user-select: none;
  cursor: default;
  padding: 4px;
`;

const AssetNodeShowOnHover = styled.span`
  display: none;
`;

export const AssetNodeBox = styled.div<{$isSource: boolean; $selected: boolean}>`
  ${(p) =>
    p.$isSource
      ? `border: 2px dashed ${p.$selected ? Colors.Gray600 : Colors.Gray300}`
      : `border: 2px solid ${p.$selected ? Colors.Blue500 : Colors.Blue200}`};

  ${(p) =>
    p.$isSource
      ? `outline: 3px solid ${p.$selected ? Colors.Gray300 : 'transparent'}`
      : `outline: 3px solid ${p.$selected ? Colors.Blue200 : 'transparent'}`};

  background: ${Colors.White};
  border-radius: 8px;
  position: relative;
  &:hover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
    ${AssetNodeShowOnHover} {
      display: initial;
    }
  }
`;
const Name = styled.div<{$isSource: boolean}>`
  /** Keep in sync with DISPLAY_NAME_PX_PER_CHAR */
  display: flex;
  padding: 3px 6px;
  background: ${(p) => (p.$isSource ? Colors.Gray100 : Colors.Blue50)};
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 7px;
  border-top-right-radius: 7px;
  font-weight: 600;
  gap: 4px;
`;

const MinimalAssetNodeContainer = styled(AssetNodeContainer)`
  height: 100%;
`;

const MinimalAssetNodeBox = styled.div<{
  $isSource: boolean;
  $selected: boolean;
  $background: string;
  $border: string;
}>`
  background: ${(p) => p.$background};
  ${(p) =>
    p.$isSource
      ? `border: 4px dashed ${p.$selected ? Colors.Gray500 : p.$border}`
      : `border: 4px solid ${p.$selected ? Colors.Blue500 : p.$border}`};

  ${(p) =>
    p.$isSource
      ? `outline: 8px solid ${p.$selected ? Colors.Gray300 : 'transparent'}`
      : `outline: 8px solid ${p.$selected ? Colors.Blue200 : 'transparent'}`};

  border-radius: 10px;
  position: relative;
  padding: 4px;
  height: 100%;
  min-height: 46px;
  &:hover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const MinimalName = styled(Name)`
  font-weight: 600;
  white-space: nowrap;
  position: absolute;
  background: none;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
`;

const Description = styled.div<{$color: string}>`
  padding: 6px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: ${(p) => p.$color};
  border-top: 1px solid ${Colors.Blue50};
  background: ${Colors.White};
  font-size: 12px;
`;

const Stats = styled.div`
  padding: 4px 8px;
  border-top: 1px solid ${Colors.Blue50};
  background: ${Colors.White};
  font-size: 12px;
  line-height: 20px;
`;

const StatsRow = styled.div`
  display: flex;
  justify-content: space-between;
  min-height: 18px;
  & > span {
    color: ${Colors.Gray800};
  }
`;
