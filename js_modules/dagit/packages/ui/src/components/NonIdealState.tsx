import * as React from 'react';

import {Box} from './Box';
import {Colors} from './Colors';
import {IconName, Icon} from './Icon';
import {Spinner} from './Spinner';
import {Subheading} from './Text';

export type NonIdealStateProps = React.DetailedHTMLProps<
  React.InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
> & {
  icon: 'error' | 'no-results' | 'spinner' | IconName;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  shrinkable?: boolean;
};

export const NonIdealState: React.FC<NonIdealStateProps> = ({
  title,
  description,
  icon,
  action,
  shrinkable,
}) => {
  const singleContentElement = [title, description, action].filter(Boolean).length === 1;

  return (
    <Box
      flex={{gap: 20, alignItems: singleContentElement ? 'center' : 'flex-start'}}
      background={Colors.Gray50}
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
        <Icon name="search" size={48} color={Colors.Gray400} />
      ) : (
        <Icon name={icon} size={48} color={Colors.Gray400} />
      )}
      <Box
        flex={{
          gap: 8,
          direction: 'column',
          alignItems: 'flex-start',
        }}
      >
        {title && <Subheading style={{color: Colors.Gray900}}>{title}</Subheading>}
        {description && <div style={{color: Colors.Gray500}}>{description}</div>}
        {action}
      </Box>
    </Box>
  );
};
