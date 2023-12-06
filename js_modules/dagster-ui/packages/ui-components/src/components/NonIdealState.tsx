import * as React from 'react';

import {colorAccentGray, colorBackgroundLight, colorTextDefault} from '../theme/color';

import {Box} from './Box';
import {IconName, Icon} from './Icon';
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
      background={colorBackgroundLight()}
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
        <Icon name="search" size={48} color={colorAccentGray()} />
      ) : icon ? (
        <Icon name={icon} size={48} color={colorAccentGray()} />
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
        {title && <Subheading style={{color: colorTextDefault()}}>{title}</Subheading>}
        {description && <div style={{color: colorTextDefault()}}>{description}</div>}
        {action}
      </Box>
    </Box>
  );
};
