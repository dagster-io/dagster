import {useMutation} from '@apollo/client';
import {ContextMenu2 as ContextMenu} from '@blueprintjs/popover2';
import qs from 'query-string';
import React, {CSSProperties} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AppContext} from '../../app/AppContext';
import {showLaunchError} from '../../execute/showLaunchError';
import {SVGNodeTag} from '../../graph/SolidTags';
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
      <div
        style={{
          outline: selected
            ? `2px dashed rgba(255, 69, 0, 1)`
            : secondaryHighlight
            ? `2px solid ${ColorsWIP.Blue500}55`
            : 'none',
          outlineOffset: 0,
          padding: 4,
          marginTop: 10,
          marginRight: 4,
          marginLeft: 4,
          marginBottom: 2,
          position: 'absolute',
          background: selected ? 'rgba(255, 69, 0, 0.2)' : 'white',
          inset: 0,
        }}
      >
        <div style={{border: `1px solid ${ColorsWIP.Gray200}`, position: 'relative'}}>
          <div
            style={{
              display: 'flex',
              padding: '4px 8px',
              fontFamily: FontFamily.monospace,
              background: ColorsWIP.White,
              fontWeight: 600,
            }}
          >
            {assetKeyToString(definition.assetKey)}
            <div style={{flex: 1}} />
            {computeStatus === 'old' && (
              <div
                style={{
                  color: '#f58f52',
                  lineHeight: '10px',
                  fontSize: '11px',
                  textAlign: 'right',
                  marginTop: -4,
                  marginBottom: -4,
                  padding: '2.5px 5px',
                  marginRight: -9,
                  borderRight: '3px solid #f58f52',
                }}
              >
                upstream
                <br />
                changed
              </div>
            )}
          </div>
          {definition.description && (
            <div
              style={{
                background: '#EFF4F7',
                padding: '4px 8px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                borderTop: '1px solid #ccc',
                fontSize: 12,
              }}
            >
              {markdownToPlaintext(definition.description).split('\n')[0]}
            </div>
          )}
          {event ? (
            <AssetNodeStats>
              {runOrError.__typename === 'PipelineRun' && (
                <AssetNodeStatsRow>
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
                </AssetNodeStatsRow>
              )}

              <AssetNodeStatsRow>
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
              </AssetNodeStatsRow>
            </AssetNodeStats>
          ) : (
            <AssetNodeStats>
              <AssetNodeStatsRow style={{opacity: 0.5}}>
                <span>No materializations</span>
                <span>—</span>
              </AssetNodeStatsRow>
              <AssetNodeStatsRow style={{opacity: 0.5}}>
                <span>—</span>
                <span>—</span>
              </AssetNodeStatsRow>
            </AssetNodeStats>
          )}
          {kind && (
            <svg
              height={20}
              width={100}
              viewBox="0 0 100 20"
              style={{position: 'absolute', left: -1, bottom: -20}}
            >
              <SVGNodeTag
                tag={{
                  label: kind,
                  onClick: () => {
                    window.requestAnimationFrame(() =>
                      document.dispatchEvent(new Event('show-kind-info')),
                    );
                  },
                }}
                minified={false}
                height={20}
              />
            </svg>
          )}
        </div>
      </div>
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

const AssetNodeStats = styled.div`
  background: #e1eaf0;
  padding: 4px 8px;
  border-top: 1px solid #ccc;
  font-size: 12px;
  line-height: 18px;
`;

const AssetNodeStatsRow = styled.div`
  display: flex;
  justify-content: space-between;
  min-height: 14px;
`;
