import {FontFamily, Spinner, Tooltip} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {LiveDataForNode} from './Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetViewParams} from '../assets/types';
import {AssetKeyInput} from '../graphql/types';
import {linkToRunEvent, titleForRun} from '../runs/RunUtils';

interface AssetLatestRunSpinnerProps {
  liveData?: LiveDataForNode;
  purpose?: 'caption-text' | 'body-text' | 'section';
}

export const AssetLatestRunSpinner = ({
  liveData,
  purpose = 'body-text',
}: AssetLatestRunSpinnerProps) => {
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

interface AssetRunLinkProps {
  runId: string;
  assetKey: AssetKeyInput;
  children?: React.ReactNode;
  event?: Parameters<typeof linkToRunEvent>[1];
}

export const AssetRunLink = ({assetKey, runId, children, event}: AssetRunLinkProps) => {
  const content = children || (
    <span style={{fontSize: '1.2em', fontFamily: FontFamily.monospace}}>
      {titleForRun({id: runId})}
    </span>
  );

  const buildLink = () => {
    if (runId === '') {
      // reported event
      const params: AssetViewParams = event
        ? {view: 'events', time: `${event.timestamp}`}
        : {view: 'events'};
      return assetDetailsPathForKey(assetKey, params);
    }
    return event ? linkToRunEvent({id: runId}, event) : `/runs/${runId}`;
  };

  return (
    <Link to={buildLink()} target="_blank" rel="noreferrer">
      {content}
    </Link>
  );
};
