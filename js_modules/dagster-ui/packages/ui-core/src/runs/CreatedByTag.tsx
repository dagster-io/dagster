import {Box, Tag} from '@dagster-io/ui-components';
import {memo} from 'react';
import {Link} from 'react-router-dom';
import {UserDisplay} from 'shared/runs/UserDisplay.oss';
import styled from 'styled-components';

// import {DagsterTag} from './RunTag';
import {RunFilterToken} from './RunsFilterInput';
import {LaunchedByFragment} from './types/launchedByFragment.types';
import {TagActionsPopover} from '../ui/TagActions';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

type Props = {
  repoAddress?: RepoAddress | null;
  // tags: RunTagsFragment[];
  launchedBy: LaunchedByFragment;
  onAddTag?: (token: RunFilterToken) => void;
};

export const CreatedByTagCell = memo(({repoAddress, launchedBy, onAddTag}: Props) => {
  return (
    <CreatedByTagCellWrapper flex={{direction: 'column', alignItems: 'flex-start'}}>
      <CreatedByTag repoAddress={repoAddress} launchedBy={launchedBy} onAddTag={onAddTag} />
    </CreatedByTagCellWrapper>
  );
});

export const CreatedByTagCellWrapper = styled(Box)``;

// type TagType =
//   | {
//       type: 'user' | 'schedule' | 'sensor' | 'auto-materialize' | 'auto-observe';
//       tag: RunTagsFragment;
//     }
//   | {type: 'manual'};

// const pluckTagFromList = (tags: RunTagsFragment[]): TagType => {
//   // Prefer user/schedule/sensor
//   for (const tag of tags) {
//     const {key} = tag;
//     switch (key) {
//       case DagsterTag.User:
//         return {type: 'user', tag};
//       case DagsterTag.ScheduleName:
//         return {type: 'schedule', tag};
//       case DagsterTag.SensorName:
//         return {type: 'sensor', tag};
//     }
//   }

//   // If none of those, check for AMP
//   for (const tag of tags) {
//     const {key} = tag;
//     switch (key) {
//       case DagsterTag.Automaterialize:
//         return {type: 'auto-materialize', tag};
//       case DagsterTag.CreatedBy: {
//         // Backwards compatibility
//         if (tag.value === 'auto_materialize') {
//           return {type: 'auto-materialize', tag};
//         } else {
//           continue;
//         }
//       }
//       case DagsterTag.AutoObserve:
//         return {type: 'auto-observe', tag};
//     }
//   }

//   return {type: 'manual'};
// };

export const CreatedByTag = ({repoAddress, launchedBy, onAddTag}: Props) => {
  const {kind, tag} = launchedBy;
  const {key, value} = tag;

  if (kind === 'manual') {
    return <Tag icon="account_circle">Manually launched</Tag>;
  }

  const buildTagElement = () => {
    switch (kind) {
      case 'user':
        return <UserDisplay email={value} />;
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
    return <Tag icon="auto_observe">Auto-observation</Tag>; // TODO fix - unreachable but not sure what to put here
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
