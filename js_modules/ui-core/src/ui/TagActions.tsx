import {Box, Colors, Popover, Text} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import styles from './css/TagActions.module.css';
import {TagType} from '../runs/RunTag';

export type TagAction =
  | {
      label: React.ReactNode;
      onClick: (tag: TagType) => any; // click action
    }
  | {
      label: React.ReactNode;
      to: string; // link-style action (supports cmd-click for new tab)
      disabled?: boolean; // render greyed out and non-navigable (e.g. data still loading)
    };

export const TagActions = ({data, actions}: {data: TagType; actions: TagAction[]}) => (
  <Box
    className={styles.actionContainer}
    background={Colors.tooltipBackground()}
    flex={{direction: 'row'}}
  >
    {actions.map((action, ii) =>
      'to' in action ? (
        action.disabled ? (
          <button key={ii} className={styles.tagButton} disabled>
            <Text size={12}>{action.label}</Text>
          </button>
        ) : (
          <Link to={action.to} key={ii} className={styles.tagButtonLink}>
            <Text size={12}>{action.label}</Text>
          </Link>
        )
      ) : (
        <button key={ii} className={styles.tagButton} onClick={() => action.onClick(data)}>
          <Text size={12}>{action.label}</Text>
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
  onOpening,
}: {
  data: TagType;
  actions: TagAction[];
  children: React.ReactNode;
  childrenMiddleTruncate?: boolean;
  onOpening?: () => void;
}) => {
  return (
    <Popover
      content={<TagActions actions={actions} data={data} />}
      hoverOpenDelay={100}
      hoverCloseDelay={100}
      targetProps={childrenMiddleTruncate ? {style: {minWidth: 0, maxWidth: '100%'}} : {}}
      placement="top"
      interactionKind="hover"
      onOpening={onOpening}
    >
      {children}
    </Popover>
  );
};
