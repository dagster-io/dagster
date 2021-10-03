import * as React from 'react';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconName, IconWIP} from './Icon';
import {Subheading} from './Text';

type Props = React.DetailedHTMLProps<
  React.InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
> & {
  icon: IconName;
  title?: string;
  description: React.ReactNode;
  action?: React.ReactNode;
};

export const NonIdealState: React.FC<Props> = ({title, description, icon, action}) => {
  return (
    <Box
      flex={{gap: 20, alignItems: 'flex-start'}}
      background={ColorsWIP.Gray50}
      padding={24}
      style={{
        margin: 'auto',
        borderRadius: 8,
        width: 'max-content',
        maxWidth: 500,
      }}
    >
      <IconWIP name={icon} size={48} color={ColorsWIP.Gray400} />
      <Box flex={{gap: 8, direction: 'column'}}>
        {title && <Subheading style={{color: ColorsWIP.Gray900}}>{title}</Subheading>}
        <div style={{color: ColorsWIP.Gray500}}>{description}</div>
        {action}
      </Box>
    </Box>
  );
};
