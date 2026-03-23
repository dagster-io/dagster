// eslint-disable-next-line no-restricted-imports
import {Dialog as BlueprintDialog} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from './Box';
import {Colors} from './Color';
import {ErrorBoundary} from './ErrorBoundary';
import {Icon, IconName} from './Icon';
import {UnstyledButton} from './UnstyledButton';

interface Props extends Omit<
  React.ComponentProps<typeof BlueprintDialog>,
  'title' | 'icon' | 'backdropClassName'
> {
  children: React.ReactNode;
  title?: React.ReactNode;
  icon?: IconName;
}

export const Dialog = (props: Props) => {
  const {icon, title, children, isCloseButtonShown, onClose, ...rest} = props;
  return (
    <BlueprintDialog
      {...rest}
      portalClassName={`dagster-portal${props.portalClassName ? ` ${props.portalClassName}` : ''}`}
      backdropClassName="dagster-backdrop"
      className={`dagster-dialog${props.className ? ` ${props.className}` : ''}`}
      onClose={onClose}
    >
      {title ? (
        <DialogHeader
          icon={icon}
          label={title}
          isCloseButtonShown={isCloseButtonShown}
          onClose={onClose}
        />
      ) : null}
      <ErrorBoundary region="dialog">{children}</ErrorBoundary>
    </BlueprintDialog>
  );
};

interface HeaderProps {
  label: React.ReactNode;
  icon?: IconName;
  right?: React.ReactNode;
  isCloseButtonShown?: boolean;
  onClose?: Props['onClose'];
}

export const DialogHeader = (props: HeaderProps) => {
  const {icon, label, right, isCloseButtonShown, onClose} = props;
  return (
    <Box
      background={Colors.backgroundDefault()}
      padding={{vertical: 16, horizontal: 20}}
      border="bottom"
    >
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        {icon ? <Icon name={icon} color={Colors.accentPrimary()} /> : null}
        <DialogHeaderText>{label}</DialogHeaderText>
        {right}
        {isCloseButtonShown ? (
          <UnstyledButton onClick={onClose}>
            <Icon name="close" />
          </UnstyledButton>
        ) : null}
      </Box>
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
