import {Dialog as BlueprintDialog} from '@blueprintjs/core';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components/macro';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconName, IconWIP} from './Icon';

interface Props extends Omit<React.ComponentProps<typeof BlueprintDialog>, 'backdropClassName'> {}

export const DialogWIP: React.FC<Props> = (props) => {
  const {...rest} = props;
  return <BlueprintDialog {...rest} backdropClassName="dagit-backdrop" className="dagit-dialog" />;
};

interface HeaderProps {
  icon?: IconName;
  label: React.ReactNode;
}

export const DialogHeader: React.FC<HeaderProps> = (props) => {
  const {icon, label} = props;
  return (
    <Box
      background={ColorsWIP.Gray50}
      padding={{vertical: 16, horizontal: 20}}
      border={{side: 'bottom', width: 1, color: ColorsWIP.Gray200}}
    >
      <Group direction="row" spacing={8} alignItems="center">
        {icon ? <IconWIP name={icon} color={ColorsWIP.Gray800} /> : null}
        <DialogHeaderText>{label}</DialogHeaderText>
      </Group>
    </Box>
  );
};

export const DialogBody: React.FC = (props) => {
  return (
    <Box padding={{vertical: 16, horizontal: 20}} background={ColorsWIP.White}>
      {props.children}
    </Box>
  );
};

interface DialogFooterProps {
  right?: React.ReactNode;
  left?: React.ReactNode;
}

export const DialogFooter: React.FC<DialogFooterProps> = (props) => {
  return (
    <Box
      padding={{bottom: 20, top: 8, horizontal: 20}}
      background={ColorsWIP.White}
      flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
    >
      <div>{props.left}</div>
      <div>{props.right}</div>
    </Box>
  );
};

export const DialogButtons: React.FC = (props) => {
  return (
    <Group direction="row" spacing={12} alignItems="center">
      {props.children}
    </Group>
  );
};

const DialogHeaderText = styled.div`
  font-size: 16px;
  font-weight: 500;
`;

export const GlobalDialogStyle = createGlobalStyle`
  .bp3-overlay-backdrop {
    background-color: rgba(189, 186, 183, 0.7);
  }

  .bp3-dialog-container {
    display: grid;
    grid-template-rows: minmax(40px, 1fr) auto minmax(40px, 2fr);
    grid-template-columns: 40px 8fr 40px;
  }

  .bp3-dialog {
    background-color: ${ColorsWIP.White};
    border-radius: 4px;
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px;
    grid-row: 2;
    grid-column: 2;
    margin: 0 auto;
    padding: 0;
  }

  .bp3-dialog > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  .bp3-dialog > :last-child {
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: 4px;
  }

  .bp3-dialog-container.bp3-overlay-enter > .bp3-dialog,
  .bp3-dialog-container.bp3-overlay-appear > .bp3-dialog {
    opacity: 0;
    transform:scale(0.95);
  }

  .bp3-dialog-container.bp3-overlay-enter-active > .bp3-dialog,
  .bp3-dialog-container.bp3-overlay-appear-active > .bp3-dialog {
    opacity: 1;
    transform: scale(1);
    transition-delay: 0;
    transition-duration: 150ms;
    transition-property: opacity, transform;
    transition-timing-function: ease-in-out;
  }

  .bp3-dialog-container.bp3-overlay-exit > .bp3-dialog {
    opacity: 1;
    transform: scale(1);
  }

  .bp3-dialog-container.bp3-overlay-exit-active > .bp3-dialog{
    opacity: 0;
    transform: scale(0.95);
    transition-delay:0;
    transition-duration: 150ms;
    transition-property: opacity, transform;
    transition-timing-function: ease-in-out;
  }
`;
