// eslint-disable-next-line no-restricted-imports
import {Dialog as BlueprintDialog} from '@blueprintjs/core';
import * as React from 'react';
import styled, {createGlobalStyle} from 'styled-components';

import {Box} from './Box';
import {Colors} from './Color';
import {ErrorBoundary} from './ErrorBoundary';
import {Group} from './Group';
import {Icon, IconName} from './Icon';

interface Props
  extends Omit<
    React.ComponentProps<typeof BlueprintDialog>,
    'title' | 'icon' | 'backdropClassName'
  > {
  children: React.ReactNode;
  title?: React.ReactNode;
  icon?: IconName;
}

export const Dialog = (props: Props) => {
  const {icon, title, children, ...rest} = props;
  return (
    <BlueprintDialog
      {...rest}
      portalClassName={`dagster-portal${props.portalClassName ? ` ${props.portalClassName}` : ''}`}
      backdropClassName="dagster-backdrop"
      className={`dagster-dialog${props.className ? ` ${props.className}` : ''}`}
    >
      {title ? <DialogHeader icon={icon} label={title} /> : null}
      <ErrorBoundary region="dialog">{children}</ErrorBoundary>
    </BlueprintDialog>
  );
};

interface HeaderProps {
  icon?: IconName;
  label: React.ReactNode;
}

export const DialogHeader = (props: HeaderProps) => {
  const {icon, label} = props;
  return (
    <Box
      background={Colors.backgroundDefault()}
      padding={{vertical: 16, horizontal: 20}}
      border="bottom"
    >
      <Group direction="row" spacing={8} alignItems="center">
        {icon ? <Icon name={icon} color={Colors.accentPrimary()} /> : null}
        <DialogHeaderText>{label}</DialogHeaderText>
      </Group>
    </Box>
  );
};

interface BodyProps {
  children: React.ReactNode;
}

export const DialogBody = ({children, ...rest}: BodyProps) => {
  return (
    <Box padding={{vertical: 16, horizontal: 20}} background={Colors.backgroundDefault()} {...rest}>
      {children}
    </Box>
  );
};

interface DialogFooterProps {
  children: React.ReactNode;
  topBorder?: boolean;
  left?: React.ReactNode;
}

export const DialogFooter = ({children, left, topBorder}: DialogFooterProps) => {
  return (
    <Box
      padding={{bottom: 16, top: topBorder ? 16 : 8, horizontal: 20}}
      border={topBorder ? 'top' : null}
      background={Colors.backgroundDefault()}
      flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
    >
      <div>{left}</div>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>{children}</Box>
    </Box>
  );
};

export const DialogHeaderText = styled.div`
  font-size: 16px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
`;

export const GlobalDialogStyle = createGlobalStyle`
  .dagster-portal .bp5-overlay-backdrop {
    background-color: ${Colors.dialogBackground()};
  }

  .dagster-portal .bp5-dialog-container {
    display: grid;
    grid-template-rows: minmax(40px, 1fr) auto minmax(40px, 2fr);
    grid-template-columns: 40px 8fr 40px;
  }

  .dagster-portal .bp5-dialog {
    background-color: ${Colors.backgroundDefault()};
    border-radius: 4px;
    box-shadow: ${Colors.shadowDefault()} 0px 2px 12px;
    grid-row: 2;
    grid-column: 2;
    margin: 0 auto;
    overflow: hidden;
    padding: 0;
  }

  .dagster-portal .bp5-dialog > :first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
  }

  .dagster-portal .bp5-dialog > :last-child {
    border-bottom-right-radius: 4px;
    border-bottom-left-radius: 4px;
  }

  .dagster-portal .bp5-dialog-container.bp5-overlay-enter > .bp5-dialog,
  .dagster-portal .bp5-dialog-container.bp5-overlay-appear > .bp5-dialog {
    opacity: 0;
    transform:scale(0.95);
  }

  .dagster-portal .bp5-dialog-container.bp5-overlay-enter-active > .bp5-dialog,
  .dagster-portal .bp5-dialog-container.bp5-overlay-appear-active > .bp5-dialog {
    opacity: 1;
    transform: scale(1);
    transition-delay: 0;
    transition-duration: 150ms;
    transition-property: opacity, transform;
    transition-timing-function: ease-in-out;
  }

  .dagster-portal .bp5-dialog-container.bp5-overlay-exit > .bp5-dialog {
    opacity: 1;
    transform: scale(1);
  }

  .dagster-portal .bp5-dialog-container.bp5-overlay-exit-active > .bp5-dialog {
    opacity: 0;
    transform: scale(0.95);
    transition-delay:0;
    transition-duration: 150ms;
    transition-property: opacity, transform;
    transition-timing-function: ease-in-out;
  }
`;
