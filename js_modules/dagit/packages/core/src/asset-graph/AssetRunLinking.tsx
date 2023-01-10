import {Colors, Icon, Tooltip, Box, Spinner, Tag, CaptionMono} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {CurrentMinutesLateTag} from '../assets/CurrentMinutesLateTag';
import {titleForRun, linkToRunEvent} from '../runs/RunUtils';

import {LiveDataForNode, MISSING_LIVE_DATA} from './Utils';

export const AssetLatestRunSpinner: React.FC<{
  liveData?: LiveDataForNode;
  purpose?: 'caption-text' | 'body-text' | 'section';
}> = ({liveData, purpose = 'body-text'}) => {
  if (liveData?.inProgressRunIds?.length) {
    return (
      <Tooltip content="A run is currently rematerializing this asset.">
        <Spinner purpose={purpose} />
      </Tooltip>
    );
  }
  if (liveData?.unstartedRunIds?.length) {
    return (
      <Tooltip content="A run has started that will rematerialize this asset soon.">
        <Spinner purpose={purpose} stopped />
      </Tooltip>
    );
  }
  return null;
};

export const AssetLatestRunWithNotices: React.FC<{
  liveData?: LiveDataForNode;
  includeFreshness: boolean;
  includeRunStatus: boolean;
}> = ({liveData, includeFreshness, includeRunStatus}) => {
  const {
    lastMaterialization,
    unstartedRunIds,
    inProgressRunIds,
    runWhichFailedToMaterialize,
    stepKey,
  } = liveData || MISSING_LIVE_DATA;

  const buildRunTagContent = () => {
    if (inProgressRunIds?.length > 0) {
      return (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          {includeRunStatus && <AssetLatestRunSpinner liveData={liveData} />}
          <AssetRunLink runId={inProgressRunIds[0]} />
        </Box>
      );
    }
    if (unstartedRunIds?.length > 0) {
      return (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          {includeRunStatus && <AssetLatestRunSpinner liveData={liveData} />}
          <AssetRunLink runId={unstartedRunIds[0]} />
        </Box>
      );
    }
    if (runWhichFailedToMaterialize?.__typename === 'Run') {
      return (
        <Box flex={{gap: 4, alignItems: 'center'}}>
          {includeRunStatus && (
            <Tooltip
              content={`Run ${titleForRun({
                runId: runWhichFailedToMaterialize.id,
              })} failed to materialize this asset`}
            >
              <Icon name="warning" color={Colors.Red500} />
            </Tooltip>
          )}
          <AssetRunLink runId={runWhichFailedToMaterialize.id} />
        </Box>
      );
    }
    if (lastMaterialization) {
      return (
        <Box flex={{gap: 6, alignItems: 'center'}}>
          <AssetRunLink
            runId={lastMaterialization.runId}
            event={{stepKey, timestamp: lastMaterialization.timestamp}}
          />
        </Box>
      );
    }
    return undefined;
  };

  const runTagContent = buildRunTagContent();

  if (!includeFreshness) {
    return runTagContent || <span>–</span>;
  }

  return (
    <Box flex={{direction: 'row', gap: 4}}>
      {runTagContent ? <Tag>{runTagContent}</Tag> : <span>–</span>}
      {liveData && <CurrentMinutesLateTag liveData={liveData} policyOnHover />}
    </Box>
  );
};

export const AssetRunLink: React.FC<{
  runId: string;
  event?: Parameters<typeof linkToRunEvent>[1];
}> = ({runId, children, event}) => (
  <Link
    to={event ? linkToRunEvent({runId}, event) : `/runs/${runId}`}
    target="_blank"
    rel="noreferrer"
  >
    {children || <CaptionMono>{titleForRun({runId})}</CaptionMono>}
  </Link>
);
