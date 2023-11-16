import {Box, Caption, Popover} from '@dagster-io/ui-components';
import {CoreColors} from '@dagster-io/ui-components/src/palettes/Colors';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

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
  <ActionContainer background={CoreColors.Gray900} flex={{direction: 'row'}}>
    {actions.map((action, ii) =>
      'to' in action ? (
        <Link to={action.to} key={ii}>
          <TagButton>
            <Caption>{action.label}</Caption>
          </TagButton>
        </Link>
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
}: {
  data: TagType;
  actions: TagAction[];
  children: React.ReactNode;
}) => {
  return (
    <Popover
      content={<TagActions actions={actions} data={data} />}
      hoverOpenDelay={100}
      hoverCloseDelay={100}
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

const TagButton = styled.button`
  border: none;
  background: ${CoreColors.Gray900};
  color: ${CoreColors.Gray100};
  cursor: pointer;
  padding: 8px 12px;
  text-align: left;

  :not(:last-child) {
    box-shadow: -1px 0 0 inset ${CoreColors.Gray600};
  }

  :focus {
    outline: none;
  }

  :hover {
    background-color: ${CoreColors.Gray800};
    color: ${CoreColors.White};
  }
`;
