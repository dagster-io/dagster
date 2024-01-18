import React from 'react';
import {Link} from 'react-router-dom';

import {Box, Tag} from '@dagster-io/ui-components';

import {useLaunchPadHooks} from '../launchpad/LaunchpadHooksContext';
import {TagActionsPopover} from '../ui/TagActions';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';
import {DagsterTag} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';
import {RunTagsFragment} from './types/RunTable.types';

type Props = {
  repoAddress?: RepoAddress | null;
  tags: RunTagsFragment[];
  onAddTag?: (token: RunFilterToken) => void;
};

export const CreatedByTagCell = React.memo(({repoAddress, tags, onAddTag}: Props) => {
  return (
    <Box flex={{direction: 'column', alignItems: 'flex-start'}}>
      <CreatedByTag repoAddress={repoAddress} tags={tags} onAddTag={onAddTag} />
    </Box>
  );
});

type TagType =
  | {
      type: 'user' | 'schedule' | 'sensor' | 'auto-materialize' | 'auto-observe';
      tag: RunTagsFragment;
    }
  | {type: 'manual'};

const pluckTagFromList = (tags: RunTagsFragment[]): TagType => {
  for (const tag of tags) {
    const {key} = tag;
    switch (key) {
      case DagsterTag.User:
        return {type: 'user', tag};
      case DagsterTag.ScheduleName:
        return {type: 'schedule', tag};
      case DagsterTag.SensorName:
        return {type: 'sensor', tag};
      case DagsterTag.Automaterialize:
        return {type: 'auto-materialize', tag};
      case DagsterTag.CreatedBy: {
        // Backwards compatibility
        if (tag.value === 'auto_materialize') {
          return {type: 'auto-materialize', tag};
        } else {
          continue;
        }
      }
      case DagsterTag.AutoObserve:
        return {type: 'auto-observe', tag};
    }
  }

  return {type: 'manual'};
};

export const CreatedByTag = ({repoAddress, tags, onAddTag}: Props) => {
  const {UserDisplay} = useLaunchPadHooks();

  const plucked = pluckTagFromList(tags);

  if (plucked.type === 'manual') {
    return <Tag icon="account_circle">Manually launched</Tag>;
  }

  const buildTagElement = () => {
    const {type, tag} = plucked;
    const {value} = tag;
    switch (type) {
      case 'user':
        return <UserDisplay email={tag.value} />;
      case 'schedule': {
        return (
          <Tag icon="schedule">
            {repoAddress ? (
              <Link to={workspacePathFromAddress(repoAddress, `/schedules/${value}`)}>{value}</Link>
            ) : (
              value
            )}
          </Tag>
        );
      }
      case 'sensor': {
        return (
          <Tag icon="sensors">
            {repoAddress ? (
              <Link to={workspacePathFromAddress(repoAddress, `/sensors/${value}`)}>{value}</Link>
            ) : (
              value
            )}
          </Tag>
        );
      }
      case 'auto-materialize':
        return <Tag icon="auto_materialize_policy">Auto-materialize policy</Tag>;
      case 'auto-observe':
        return <Tag icon="auto_observe">Auto-observation</Tag>;
    }
  };

  const tagElement = buildTagElement();
  if (!onAddTag) {
    return tagElement;
  }

  const {tag} = plucked;
  const {key, value} = tag;
  return (
    <TagActionsPopover
      data={tag}
      actions={[
        {
          label: 'Add to filter',
          onClick: () => onAddTag({token: 'tag', value: `${key}=${value}`}),
        },
      ]}
    >
      {tagElement}
    </TagActionsPopover>
  );
};
