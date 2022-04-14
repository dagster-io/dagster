import {gql} from '@apollo/client';
import {Colors, Icon, Spinner, Tooltip, FontFamily, Box} from '@dagster-io/ui';
import {isEqual} from 'lodash';
import qs from 'qs';
import React, {CSSProperties} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {LATEST_MATERIALIZATION_METADATA_FRAGMENT} from '../assets/LastMaterializationMetadata';
import {NodeHighlightColors} from '../graph/OpNode';
import {OpTags} from '../graph/OpTags';
import {METADATA_ENTRY_FRAGMENT} from '../metadata/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {markdownToPlaintext} from '../ui/markdownToPlaintext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {displayNameForAssetKey, LiveDataForNode, isAssetGroup} from './Utils';
import {AssetNodeFragment} from './types/AssetNodeFragment';

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  metadata: {key: string; value: string}[];
  selected: boolean;
  inAssetCatalog?: boolean;
}> = React.memo(({definition, metadata, selected, liveData, inAssetCatalog}) => {
  const event = liveData?.lastMaterialization;
  const runOrError = event?.runOrError;
  const kind = metadata.find((m) => m.key === 'kind')?.value;
  const repoAddress = buildRepoAddress(
    definition.repository.name,
    definition.repository.location.name,
  );

  const displayName = displayNameForAssetKey(definition.assetKey);

  return (
    <AssetNodeContainer $selected={selected}>
      <AssetNodeBox>
        <Name>
          <span style={{marginTop: 1}}>
            <Icon name="asset" />
          </span>
          <div style={{overflow: 'hidden', textOverflow: 'ellipsis', marginTop: -1}}>
            {displayName}
          </div>
          <div style={{flex: 1}} />
          {liveData && liveData.inProgressRunIds.length > 0 ? (
            <Tooltip content="A run is currently rematerializing this asset.">
              <Spinner purpose="body-text" />
            </Tooltip>
          ) : liveData && liveData.unstartedRunIds.length > 0 ? (
            <Tooltip content="A run has started that will rematerialize this asset soon.">
              <Spinner purpose="body-text" stopped />
            </Tooltip>
          ) : liveData &&
            (liveData.runWhichFailedToMaterialize || liveData.runsSinceMaterialization) ? (
            <Tooltip content="This asset was not materialized by one or more recent runs.">
              <Icon name="warning" color={Colors.Gray400} />
            </Tooltip>
          ) : undefined}

          {liveData?.computeStatus === 'old' && (
            <UpstreamNotice>
              upstream
              <br />
              changed
            </UpstreamNotice>
          )}
        </Name>
        {definition.description && !inAssetCatalog && (
          <Description>{markdownToPlaintext(definition.description).split('\n')[0]}</Description>
        )}
        <Stats>
          {runOrError?.__typename === 'Run' && event ? (
            <>
              <StatsRow>
                {isAssetGroup(runOrError.pipelineName) ? (
                  <span />
                ) : (
                  <Link
                    data-tooltip={runOrError.pipelineName}
                    data-tooltip-style={RunLinkTooltipStyle}
                    style={{overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: 8}}
                    target={inAssetCatalog ? '_blank' : undefined}
                    onClick={(e) => e.stopPropagation()}
                    to={
                      repoAddress.name
                        ? workspacePath(
                            repoAddress.name,
                            repoAddress.location,
                            `jobs/${runOrError.pipelineName}`,
                          )
                        : workspacePipelinePathGuessRepo(runOrError.pipelineName, true, '')
                    }
                  >
                    {runOrError.pipelineName}
                  </Link>
                )}
                <Link
                  style={{fontFamily: FontFamily.monospace, fontSize: 14}}
                  to={`/instance/runs/${runOrError.runId}?${qs.stringify({
                    timestamp: event.stepStats.endTime,
                    selection: event.stepStats.stepKey,
                    logs: `step:${event.stepStats.stepKey}`,
                  })}`}
                  onClick={(e) => e.stopPropagation()}
                  target="_blank"
                >
                  {titleForRun({runId: runOrError.runId})}
                </Link>
              </StatsRow>
              <StatsRow>
                {event.stepStats.endTime ? (
                  <TimestampDisplay
                    timestamp={event.stepStats.endTime}
                    timeFormat={{showSeconds: false, showTimezone: false}}
                  />
                ) : (
                  'Never'
                )}
                <TimeElapsed
                  startUnix={event.stepStats.startTime}
                  endUnix={event.stepStats.endTime}
                />
              </StatsRow>
            </>
          ) : (
            <>
              <StatsRow style={{opacity: 0.5}}>
                <span>No materializations</span>
                <span>—</span>
              </StatsRow>
              <StatsRow style={{opacity: 0.5}}>
                <span>—</span>
                <span>—</span>
              </StatsRow>
            </>
          )}
          {definition.opName && displayName !== definition.opName && (
            <StatsRow>
              <Box
                flex={{gap: 4, alignItems: 'flex-end'}}
                style={{marginLeft: -2, overflow: 'hidden'}}
              >
                <Icon name="op" size={16} />
                <div
                  style={{
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {definition.opName}
                </div>
              </Box>
            </StatsRow>
          )}
        </Stats>
        {kind && (
          <OpTags
            minified={false}
            style={{right: -2, paddingTop: 5}}
            tags={[
              {
                label: kind,
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
  );
}, isEqual);

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opName
    repository {
      id
      name
      location {
        id
        name
      }
    }
    assetKey {
      path
    }
    assetMaterializations(limit: 1) {
      ...LatestMaterializationMetadataFragment

      metadataEntries {
        ...MetadataEntryFragment
      }
      stepStats {
        stepKey
        startTime
        endTime
      }
      runOrError {
        ... on PipelineRun {
          id
          runId
          status
          pipelineName
        }
      }
    }
  }

  ${METADATA_ENTRY_FRAGMENT}
  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
`;

export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    opName
    description
    metadataEntries {
      ...MetadataEntryFragment
    }
    partitionDefinition
    assetKey {
      path
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

const BoxColors = {
  Divider: 'rgba(219, 219, 244, 1)',
  Description: 'rgba(245, 245, 250, 1)',
  Stats: 'rgba(236, 236, 248, 1)',
};

const RunLinkTooltipStyle = JSON.stringify({
  background: BoxColors.Stats,
  padding: '4px 8px',
  marginLeft: -10,
  marginTop: -8,
  fontSize: 13,
  color: Colors.Link,
  border: 0,
  borderRadius: 4,
} as CSSProperties);

const AssetNodeContainer = styled.div<{$selected: boolean}>`
  outline: ${(p) => (p.$selected ? `2px dashed ${NodeHighlightColors.Border}` : 'none')};
  border-radius: 6px;
  outline-offset: -1px;
  padding: 4px;
  margin-top: 10px;
  margin-right: 4px;
  margin-left: 4px;
  margin-bottom: 2px;
  background: ${(p) => (p.$selected ? NodeHighlightColors.Background : 'white')};
  inset: 0;
`;

const AssetNodeBox = styled.div`
  border: 2px solid ${Colors.Blue200};
  background: ${Colors.White};
  border-radius: 5px;
  position: relative;
  &:hover {
    box-shadow: ${Colors.Blue200} inset 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const Name = styled.div`
  display: flex;
  padding: 4px 6px;
  background: ${Colors.White};
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-weight: 600;
  gap: 4px;
`;

const Description = styled.div`
  background: ${BoxColors.Description};
  padding: 4px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-top: 1px solid ${BoxColors.Divider};
  font-size: 12px;
`;

const Stats = styled.div`
  background: ${BoxColors.Stats};
  padding: 4px 8px;
  border-top: 1px solid ${BoxColors.Divider};
  font-size: 12px;
  line-height: 18px;
`;

const StatsRow = styled.div`
  display: flex;
  justify-content: space-between;
  min-height: 14px;
`;

const UpstreamNotice = styled.div`
  background: ${Colors.Yellow200};
  color: ${Colors.Yellow700};
  line-height: 10px;
  font-size: 11px;
  text-align: right;
  margin-top: -4px;
  margin-bottom: -4px;
  padding: 2.5px 5px;
  margin-right: -6px;
  border-top-right-radius: 3px;
`;
