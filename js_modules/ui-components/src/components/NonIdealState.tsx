import * as React from 'react';
import {CSSProperties} from 'react';

import {Box} from './Box';
import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import {Spinner} from './Spinner';
import {Heading} from './Typography';

export type NonIdealStateProps = React.DetailedHTMLProps<
  React.InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
> & {
  icon?: 'error' | 'no-results' | 'spinner' | IconName;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  shrinkable?: boolean;
  maxWidth?: CSSProperties['maxWidth'];
};

export const NonIdealState = ({
  title,
  description,
  icon,
  action,
  shrinkable,
  maxWidth = 500,
}: NonIdealStateProps) => {
  const singleContentElement = [title, description, action].filter(Boolean).length === 1;

  return (
    <Box
      className="dagster-non-ideal-state"
      flex={{gap: 20, alignItems: singleContentElement ? 'center' : 'flex-start'}}
      background={Colors.backgroundLight()}
      padding={24}
      style={{
        margin: 'auto',
        borderRadius: 8,
        width: shrinkable ? 'initial' : 'max-content',
        maxWidth,
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
        {title && (
          <Heading size={14} weight={600} color="textDefault">
            {title}
          </Heading>
        )}
        {description && <div style={{color: Colors.textDefault()}}>{description}</div>}
        {action}
      </Box>
    </Box>
  );
};
