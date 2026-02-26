import {Box, Caption, Colors, Popover} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled, {css} from 'styled-components';

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
  <ActionContainer background={Colors.tooltipBackground()} flex={{direction: 'row'}}>
    {actions.map((action, ii) =>
      'to' in action ? (
        <TagButtonLink to={action.to} key={ii}>
          <Caption>{action.label}</Caption>
        </TagButtonLink>
      ) : (
        <TagButton key={ii} onClick={() => action.onClick(data)}>
          <Caption>{action.label}</Caption>
        </TagButton>
      ),
    )}
  </ActionContainer>
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

const ActionContainer = styled(Box)`
  border-radius: 8px;
  overflow: hidden;
`;

const TagButtonSharedStyles = css`
  border: none;
  background: ${Colors.tooltipBackground()};
  color: ${Colors.tooltipText()};
  cursor: pointer;
  padding: 8px 12px;
  text-align: left;
  opacity: 0.85;
  transition: opacity 50ms linear;

  :not(:last-child) {
    box-shadow: -1px 0 0 inset ${Colors.borderHover()};
  }

  :focus {
    outline: none;
  }
`;

const TagButton = styled.button`
  ${TagButtonSharedStyles}

  :hover {
    opacity: 1;
  }
`;

const TagButtonLink = styled(Link)`
  ${TagButtonSharedStyles}

  :hover {
    color: ${Colors.tooltipText()};
    text-decoration: none;
    opacity: 1;
  }
`;
