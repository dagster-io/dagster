import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconName, IconWIP} from './Icon';

export interface Props {
  intent: 'info' | 'warning' | 'error' | 'success';
  title: React.ReactNode;
  description?: React.ReactNode;
}

export const Alert: React.FC<Props> = (props) => {
  const {intent, title, description} = props;

  const {backgroundColor, borderColor, icon, iconColor} = React.useMemo(() => {
    switch (intent) {
      case 'warning':
        return {
          backgroundColor: ColorsWIP.Yellow50,
          borderColor: ColorsWIP.Yellow500,
          icon: 'warning',
          iconColor: ColorsWIP.Yellow500,
        };
      case 'error':
        return {
          backgroundColor: ColorsWIP.Red50,
          borderColor: ColorsWIP.Red500,
          icon: 'error',
          iconColor: ColorsWIP.Red500,
        };
      case 'success':
        return {
          backgroundColor: ColorsWIP.Green50,
          borderColor: ColorsWIP.Green500,
          icon: 'done',
          iconColor: ColorsWIP.Green500,
        };
      case 'info':
      default:
        return {
          backgroundColor: ColorsWIP.Gray50,
          borderColor: ColorsWIP.Blue500,
          icon: 'info',
          iconColor: ColorsWIP.Blue500,
        };
    }
  }, [intent]);

  return (
    <Box
      background={backgroundColor}
      padding={{horizontal: 16, vertical: 12}}
      style={{
        boxShadow: `inset 4px 0 ${borderColor}, inset -1px 1px ${Colors.LIGHT_GRAY3}, inset 0 -1px ${Colors.LIGHT_GRAY3}`,
      }}
    >
      <Group direction="row" spacing={12} alignItems="flex-start">
        <IconWIP name={icon as IconName} color={iconColor} />
        <Group direction="column" spacing={8}>
          <AlertTitle>{title}</AlertTitle>
          {description ? <AlertDescription>{description}</AlertDescription> : null}
        </Group>
      </Group>
    </Box>
  );
};

Alert.defaultProps = {
  intent: 'info',
};

const AlertTitle = styled.div`
  color: ${Colors.DARK_GRAY3};
  font-weight: 600;
  -webkit-font-smoothing: antialiased;
`;

const AlertDescription = styled.div`
  color: ${Colors.DARK_GRAY3};
  font-weight: 400;
`;
