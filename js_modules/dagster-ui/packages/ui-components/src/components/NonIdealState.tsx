import * as React from 'react';

import {Box} from './Box';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import {Spinner} from './Spinner';
import {Subheading} from './Text';

export type NonIdealStateProps = React.DetailedHTMLProps<
  React.InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
> & {
  icon?: 'error' | 'no-results' | 'spinner' | IconName;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  shrinkable?: boolean;
};

export const NonIdealState = ({
  title,
  description,
  icon,
  action,
  shrinkable,
}: NonIdealStateProps) => {
  const singleContentElement = [title, description, action].filter(Boolean).length === 1;

  return (
    <Box
      flex={{gap: 20, alignItems: singleContentElement ? 'center' : 'flex-start'}}
      background={Colors.backgroundLight()}
      padding={24}
      style={{
        margin: 'auto',
        borderRadius: 8,
        width: shrinkable ? 'initial' : 'max-content',
        maxWidth: 500,
      }}
    >
      {icon === 'spinner' ? (
        <Spinner purpose="section" />
      ) : icon === 'no-results' ? (
        <Icon name="search" size={48} color={Colors.accentGray()} />
      ) : icon ? (
        <Icon name={icon} size={48} color={Colors.accentGray()} />
      ) : null}
      <Box
        flex={{
          gap: 8,
          direction: 'column',
          alignItems: 'flex-start',
          shrink: 1,
          grow: 1,
        }}
      >
        {title && <Subheading style={{color: Colors.textDefault()}}>{title}</Subheading>}
        {description && <div style={{color: Colors.textDefault()}}>{description}</div>}
        {action}
      </Box>
    </Box>
  );
};
