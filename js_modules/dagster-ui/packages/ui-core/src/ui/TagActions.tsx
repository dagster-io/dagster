import {Box, Caption, Colors, Popover} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styles from './TagActions.module.css';

import {TagType} from '../runs/RunTag';

export type TagAction =
  | {
      label: React.ReactNode;
      onClick: (tag: TagType) => any; // click action
    }
  | {
      label: React.ReactNode;
      to: string; // link-style action (supports cmd-click for new tab)
    };

export const TagActions = ({data, actions}: {data: TagType; actions: TagAction[]}) => (
  <Box className={styles.actionContainer} background={Colors.tooltipBackground()} flex={{direction: 'row'}}>
    {actions.map((action, ii) =>
      'to' in action ? (
        <Link className={styles.tagButtonLink} to={action.to} key={ii}>
          <Caption>{action.label}</Caption>
        </Link>
      ) : (
        <button className={styles.tagButton} key={ii} onClick={() => action.onClick(data)}>
          <Caption>{action.label}</Caption>
        </button>
      ),
    )}
  </Box>
);

export const TagActionsPopover = ({
  data,
  actions,
  children,
  childrenMiddleTruncate,
}: {
  data: TagType;
  actions: TagAction[];
  children: React.ReactNode;
  childrenMiddleTruncate?: boolean;
}) => {
  return (
    <Popover
      content={<TagActions actions={actions} data={data} />}
      hoverOpenDelay={100}
      hoverCloseDelay={100}
      targetProps={childrenMiddleTruncate ? {style: {minWidth: 0, maxWidth: '100%'}} : {}}
      placement="top"
      interactionKind="hover"
    >
      {children}
    </Popover>
  );
};

