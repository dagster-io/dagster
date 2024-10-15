import {Box, Tag} from '@dagster-io/ui-components';
import {memo} from 'react';
import {Link} from 'react-router-dom';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

import {DagsterTag} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';
import {RunTagsFragment} from './types/RunTagsFragment.types';
import {TagActionsPopover} from '../ui/TagActions';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

type Props = {
  repoAddress?: RepoAddress | null;
  tag: RunTagsFragment;
  onAddTag?: (token: RunFilterToken) => void;
};

export const CreatedByTagCell = memo(({repoAddress, tag, onAddTag}: Props) => {
  return (
    <CreatedByTagCellWrapper flex={{direction: 'column', alignItems: 'flex-start'}}>
      <CreatedByTag repoAddress={repoAddress} tag={tag} onAddTag={onAddTag} />
    </CreatedByTagCellWrapper>
  );
});

export const CreatedByTagCellWrapper = styled(Box)``;

export const CreatedByTag = ({repoAddress, tag, onAddTag}: Props) => {
  const {key, value} = tag

  if (key === 'manual') {
    return <Tag icon="account_circle">Manually launched</Tag>;
  }

  const buildTagElement = () => {
    switch (key) {
      case DagsterTag.User:
        return <UserDisplay email={value} />;
      case DagsterTag.ScheduleName: {
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
      case DagsterTag.SensorName: {
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
      case DagsterTag.Automaterialize:
        return <Tag icon="auto_materialize_policy">Auto-materialize policy</Tag>;
      case DagsterTag.AutoObserve:
        return <Tag icon="auto_observe">Auto-observation</Tag>;
    }
    return <Tag icon="account_circle">Unknown</Tag>; // shouldn't reach
  };

  const tagElement = buildTagElement();
  if (!onAddTag) {
    return tagElement;
  }

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
