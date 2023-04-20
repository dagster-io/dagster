import {Tooltip, Spinner, FontFamily} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';

import {titleForRun, linkToRunEvent} from '../runs/RunUtils';

import {LiveDataForNode} from './Utils';

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

export const AssetRunLink: React.FC<{
  children?: React.ReactNode;
  runId: string;
  event?: Parameters<typeof linkToRunEvent>[1];
}> = ({runId, children, event}) => (
  <Link
    to={event ? linkToRunEvent({id: runId}, event) : `/runs/${runId}`}
    target="_blank"
    rel="noreferrer"
  >
    {children || (
      <span style={{fontSize: '1.2em', fontFamily: FontFamily.monospace}}>
        {titleForRun({id: runId})}
      </span>
    )}
  </Link>
);
