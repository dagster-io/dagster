import {gql} from '@apollo/client';
import {ContextMenu2 as ContextMenu} from '@blueprintjs/popover2';
import {isEqual} from 'lodash';
import qs from 'query-string';
import React, {CSSProperties} from 'react';
import {Link, useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {LATEST_MATERIALIZATION_METADATA_FRAGMENT} from '../../assets/LastMaterializationMetadata';
import {OpTags} from '../../graph/OpTags';
import {METADATA_ENTRY_FRAGMENT} from '../../runs/MetadataEntry';
import {titleForRun} from '../../runs/RunUtils';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {ColorsWIP} from '../../ui/Colors';
import {IconWIP} from '../../ui/Icon';
import {markdownToPlaintext} from '../../ui/Markdown';
import {MenuItemWIP, MenuWIP} from '../../ui/Menu';
import {Spinner} from '../../ui/Spinner';
import {Tooltip} from '../../ui/Tooltip';
import {FontFamily} from '../../ui/styles';
import {RepoAddress} from '../types';
import {workspacePath, workspacePipelinePathGuessRepo} from '../workspacePath';

import {assetKeyToString, LiveDataForNode} from './Utils';
import {AssetNodeFragment} from './types/AssetNodeFragment';
import {useLaunchSingleAssetJob} from './useLaunchSingleAssetJob';

export const AssetNode: React.FC<{
  definition: AssetNodeFragment;
  liveData?: LiveDataForNode;
  metadata: {key: string; value: string}[];
  selected: boolean;
  repoAddress: RepoAddress;
  secondaryHighlight: boolean;
}> = React.memo(({definition, metadata, selected, liveData, repoAddress, secondaryHighlight}) => {
  const launch = useLaunchSingleAssetJob();
  const history = useHistory();

  const {materializationEvent: event, runOrError} = liveData?.lastMaterialization || {};
  const kind = metadata.find((m) => m.key === 'kind')?.value;
  const notYetMaterializedRunIds = (liveData?.inProgressRunIds || []).filter(
    (runId) => (runOrError?.__typename === 'Run' ? runOrError.runId : '') !== runId,
  );

  return (
    <ContextMenu
      content={
        <MenuWIP>
          <MenuItemWIP
            icon="open_in_new"
            onClick={() => launch(repoAddress, definition)}
            text={
              <span>
                Launch run to build{' '}
                <span style={{fontFamily: 'monospace', fontWeight: 600}}>
                  {assetKeyToString(definition.assetKey)}
                </span>
              </span>
            }
          />
          <MenuItemWIP
            icon="link"
            onClick={(e) => {
              e.stopPropagation();
              history.push(`/instance/assets/${definition.assetKey.path.join('/')}`);
            }}
            text="View in Asset Catalog"
          />
        </MenuWIP>
      }
    >
      <AssetNodeContainer $selected={selected} $secondaryHighlight={secondaryHighlight}>
        <AssetNodeBox>
          <Name>
            <IconWIP name="asset" />
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>
              {assetKeyToString(definition.assetKey)}
            </div>
            <div style={{flex: 1}} />
            {notYetMaterializedRunIds.length > 0 && (
              <Tooltip
                content={
                  <div>
                    Run ID:{' '}
                    {notYetMaterializedRunIds.map((runId) => (
                      <Link to={`/instance/runs/${runId}`} key={runId}>
                        {runId}
                      </Link>
                    ))}
                  </div>
                }
              >
                <Spinner purpose="body-text" />
              </Tooltip>
            )}

            {liveData?.computeStatus === 'old' && (
              <UpstreamNotice>
                upstream
                <br />
                changed
              </UpstreamNotice>
            )}
          </Name>
          {definition.description && (
            <Description>{markdownToPlaintext(definition.description).split('\n')[0]}</Description>
          )}
          {event ? (
            <Stats>
              {runOrError?.__typename === 'Run' && (
                <StatsRow>
                  <Link
                    data-tooltip={`${runOrError.pipelineName}${
                      runOrError.mode !== 'default' ? `:${runOrError.mode}` : ''
                    }`}
                    data-tooltip-style={RunLinkTooltipStyle}
                    style={{overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: 8}}
                    to={
                      repoAddress.name
                        ? workspacePath(
                            repoAddress.name,
                            repoAddress.location,
                            `jobs/${runOrError.pipelineName}:${runOrError.mode}`,
                          )
                        : workspacePipelinePathGuessRepo(
                            `${runOrError.pipelineName}:${runOrError.mode}`,
                            true,
                            '',
                          )
                    }
                  >
                    {`${runOrError.pipelineName}${
                      runOrError.mode !== 'default' ? `:${runOrError.mode}` : ''
                    }`}
                  </Link>
                  <Link
                    style={{fontFamily: FontFamily.monospace, fontSize: 14}}
                    to={`/instance/runs/${runOrError.runId}?${qs.stringify({
                      timestamp: event.stepStats.endTime,
                      selection: event.stepStats.stepKey,
                      logs: `step:${event.stepStats.stepKey}`,
                    })}`}
                    target="_blank"
                  >
                    {titleForRun({runId: runOrError.runId})}
                  </Link>
                </StatsRow>
              )}

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
            </Stats>
          ) : (
            <Stats>
              <StatsRow style={{opacity: 0.5}}>
                <span>No materializations</span>
                <span>—</span>
              </StatsRow>
              <StatsRow style={{opacity: 0.5}}>
                <span>—</span>
                <span>—</span>
              </StatsRow>
            </Stats>
          )}
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
    </ContextMenu>
  );
}, isEqual);

export const ASSET_NODE_LIVE_FRAGMENT = gql`
  fragment AssetNodeLiveFragment on AssetNode {
    id
    opName

    assetMaterializations(limit: 1) {
      ...LatestMaterializationMetadataFragment

      materializationEvent {
        materialization {
          metadataEntries {
            ...MetadataEntryFragment
          }
        }
        stepStats {
          stepKey
          startTime
          endTime
        }
      }
      runOrError {
        ... on PipelineRun {
          id
          runId
          status
          pipelineName
          mode
        }
      }
    }
  }

  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
  ${METADATA_ENTRY_FRAGMENT}
`;

export const ASSET_NODE_FRAGMENT = gql`
  fragment AssetNodeFragment on AssetNode {
    id
    opName
    description
    jobName
    assetKey {
      path
    }
  }
`;

export const getNodeDimensions = (def: {
  assetKey: {path: string[]};
  description?: string | null;
}) => {
  let height = 95;
  if (def.description) {
    height += 25;
  }
  return {width: Math.max(250, assetKeyToString(def.assetKey).length * 9.5) + 25, height};
};

const RunLinkTooltipStyle = JSON.stringify({
  background: '#E1EAF0',
  padding: '4px 8px',
  marginLeft: -10,
  marginTop: -8,
  fontSize: 13,
  color: ColorsWIP.Link,
  border: 0,
  borderRadius: 4,
} as CSSProperties);

const AssetNodeContainer = styled.div<{$selected: boolean; $secondaryHighlight: boolean}>`
  outline: ${(p) =>
    p.$selected
      ? `2px dashed rgba(255, 69, 0, 1)`
      : p.$secondaryHighlight
      ? `2px dashed rgba(255, 69, 0, 0.5)`
      : 'none'};
  border-radius: 6px;
  outline-offset: -1px;
  padding: 4px;
  margin-top: 10px;
  margin-right: 4px;
  margin-left: 4px;
  margin-bottom: 2px;
  position: absolute;
  background: ${(p) => (p.$selected ? 'rgba(255, 69, 0, 0.2)' : 'white')};
  inset: 0;
`;

const AssetNodeBox = styled.div`
  border: 2px solid ${ColorsWIP.Blue200};
  background: ${ColorsWIP.White};
  border-radius: 5px;
  position: relative;
`;

const Name = styled.div`
  display: flex;
  padding: 4px 6px;
  align-items: center;
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-weight: 600;
  gap: 4px;
`;

const Description = styled.div`
  background: rgba(245, 245, 250, 1);
  padding: 4px 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-top: 1px solid rgba(219, 219, 244, 1);
  font-size: 12px;
`;

const Stats = styled.div`
  background: rgba(236, 236, 248, 1);
  padding: 4px 8px;
  border-top: 1px solid rgba(219, 219, 244, 1);
  font-size: 12px;
  line-height: 18px;
`;

const StatsRow = styled.div`
  display: flex;
  justify-content: space-between;
  min-height: 14px;
`;

const UpstreamNotice = styled.div`
  background: ${ColorsWIP.Yellow200};
  color: ${ColorsWIP.Yellow700};
  line-height: 10px;
  font-size: 11px;
  text-align: right;
  margin-top: -4px;
  margin-bottom: -4px;
  padding: 2.5px 5px;
  margin-right: -6px;
  border-top-right-radius: 3px;
`;
