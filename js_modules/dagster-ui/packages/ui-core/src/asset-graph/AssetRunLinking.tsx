import {Tooltip, Spinner, FontFamily} from '@dagster-io/ui-components';
import React from 'react';
import {Link} from 'react-router-dom';

import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {AssetViewParams} from '../assets/types';
import {AssetKeyInput} from '../graphql/types';
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
  runId: string;
  assetKey: AssetKeyInput;
  children?: React.ReactNode;
  event?: Parameters<typeof linkToRunEvent>[1];
}> = ({assetKey, runId, children, event}) => {
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
