import {Colors, Icon, IconName} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';

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
          backgroundColor: `${Colors.GOLD3}16`,
          borderColor: Colors.GOLD3,
          icon: 'warning-sign',
          iconColor: Colors.GOLD3,
        };
      case 'error':
        return {
          backgroundColor: `${Colors.RED3}16`,
          borderColor: Colors.RED3,
          icon: 'error',
          iconColor: Colors.RED3,
        };
      case 'success':
        return {
          backgroundColor: `${Colors.GREEN3}16`,
          borderColor: Colors.GREEN3,
          icon: 'tick-circle',
          iconColor: Colors.GREEN3,
        };
      case 'info':
      default:
        return {
          backgroundColor: Colors.LIGHT_GRAY5,
          borderColor: Colors.BLUE3,
          icon: 'info-sign',
          iconColor: Colors.BLUE3,
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
        <Icon
          icon={icon as IconName}
          iconSize={14}
          color={iconColor}
          style={{position: 'relative', top: '-1px'}}
        />
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
