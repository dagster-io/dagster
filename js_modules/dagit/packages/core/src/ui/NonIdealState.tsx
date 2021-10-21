import * as React from 'react';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconName, IconWIP} from './Icon';
import {Spinner} from './Spinner';
import {Subheading} from './Text';

export type NonIdealStateProps = React.DetailedHTMLProps<
  React.InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
> & {
  icon: 'error' | 'no-results' | 'spinner' | IconName;
  title?: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
};

export const NonIdealState: React.FC<NonIdealStateProps> = ({title, description, icon, action}) => {
  const singleContentElement = [title, description, action].filter(Boolean).length === 1;

  return (
    <Box
      flex={{gap: 20, alignItems: singleContentElement ? 'center' : 'flex-start'}}
      background={ColorsWIP.Gray50}
      padding={24}
      style={{
        margin: 'auto',
        borderRadius: 8,
        width: 'max-content',
        maxWidth: 500,
      }}
    >
      {icon === 'spinner' ? (
        <Spinner purpose="section" />
      ) : icon === 'no-results' ? (
        <IconWIP name="search" size={48} color={ColorsWIP.Gray400} />
      ) : (
        <IconWIP name={icon} size={48} color={ColorsWIP.Gray400} />
      )}
      <Box
        flex={{
          gap: 8,
          direction: 'column',
        }}
      >
        {title && <Subheading style={{color: ColorsWIP.Gray900}}>{title}</Subheading>}
        {description && <div style={{color: ColorsWIP.Gray500}}>{description}</div>}
        {action}
      </Box>
    </Box>
  );
};
