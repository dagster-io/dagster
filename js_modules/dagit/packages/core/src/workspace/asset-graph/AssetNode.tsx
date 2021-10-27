import {useMutation} from '@apollo/client';
import {ContextMenu2 as ContextMenu} from '@blueprintjs/popover2';
import qs from 'query-string';
import React, {CSSProperties} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../../app/AppContext';
import {showLaunchError} from '../../execute/showLaunchError';
import {SolidTags} from '../../graph/SolidTags';
import {PipelineExplorerSolidHandleFragment} from '../../pipelines/types/PipelineExplorerSolidHandleFragment';
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  handleLaunchResult,
  titleForRun,
} from '../../runs/RunUtils';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {LaunchPipelineExecution} from '../../runs/types/LaunchPipelineExecution';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {ColorsWIP} from '../../ui/Colors';
import {IconWIP} from '../../ui/Icon';
import {markdownToPlaintext} from '../../ui/Markdown';
import {MenuItemWIP, MenuWIP} from '../../ui/Menu';
import {FontFamily} from '../../ui/styles';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';
import {workspacePath} from '../workspacePath';

import {assetKeyToString, Status} from './Utils';
import {AssetGraphQuery_repositoryOrError_Repository_assetNodes} from './types/AssetGraphQuery';

export const AssetNode: React.FC<{
  definition: AssetGraphQuery_repositoryOrError_Repository_assetNodes;
  handle: PipelineExplorerSolidHandleFragment;
  selected: boolean;
  computeStatus: Status;
  repoAddress: RepoAddress;
  secondaryHighlight: boolean;
}> = ({definition, handle, selected, computeStatus, repoAddress, secondaryHighlight}) => {
  const [launchPipelineExecution] = useMutation<LaunchPipelineExecution>(
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
  );
  const {basePath} = React.useContext(AppContext);
  const {materializationEvent: event, runOrError} = definition.assetMaterializations[0] || {};
  const kind = handle.solid.definition.metadata.find((m) => m.key === 'kind')?.value;

  const onLaunch = async () => {
    if (!definition.jobName) {
      return;
    }

    try {
      const result = await launchPipelineExecution({
        variables: {
          executionParams: {
            selector: {
              pipelineName: definition.jobName,
              ...repoAddressToSelector(repoAddress),
            },
            mode: 'default',
            stepKeys: [definition.opName],
          },
        },
      });
      handleLaunchResult(basePath, definition.jobName, result, true);
    } catch (error) {
      showLaunchError(error as Error);
    }
  };

  return (
    <ContextMenu
      content={
        <MenuWIP>
          <MenuItemWIP
            text={
              <span>
                Launch run to build{' '}
                <span style={{fontFamily: 'monospace', fontWeight: 600}}>
                  {assetKeyToString(definition.assetKey)}
                </span>
              </span>
            }
            icon="open_in_new"
            onClick={onLaunch}
          />
        </MenuWIP>
      }
    >
      <AssetNodeContainer $selected={selected} $secondaryHighlight={secondaryHighlight}>
        <AssetNodeBox>
          <Name>
            <IconWIP name="asset" style={{marginRight: 4}} />
            {assetKeyToString(definition.assetKey)}
            <div style={{flex: 1}} />
            {computeStatus === 'old' && (
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
              {runOrError.__typename === 'Run' && (
                <StatsRow>
                  <Link
                    data-tooltip={`${runOrError.pipelineName}${
                      runOrError.mode !== 'default' ? `:${runOrError.mode}` : ''
                    }`}
                    data-tooltip-style={RunLinkTooltipStyle}
                    style={{overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: 8}}
                    to={workspacePath(
                      repoAddress.name,
                      repoAddress.location,
                      `jobs/${runOrError.pipelineName}:${runOrError.mode}`,
                    )}
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
            <SolidTags
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
};

export const getNodeDimensions = (def: AssetGraphQuery_repositoryOrError_Repository_assetNodes) => {
  let height = 92 + 20;
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
      ? `2px solid ${ColorsWIP.Blue500}55`
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
  font-family: ${FontFamily.monospace};
  border-top-left-radius: 5px;
  border-top-right-radius: 5px;
  font-weight: 600;
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
