import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconName, IconWIP} from './Icon';

export type AlertIntent = 'info' | 'warning' | 'error' | 'success';

interface Props {
  intent: AlertIntent;
  title: React.ReactNode;
  description?: React.ReactNode;
}

export const Alert: React.FC<Props> = (props) => {
  const {intent, title, description} = props;

  const {backgroundColor, borderColor, icon, iconColor, textColor} = React.useMemo(() => {
    switch (intent) {
      case 'warning':
        return {
          backgroundColor: ColorsWIP.Yellow50,
          borderColor: ColorsWIP.Yellow500,
          icon: 'warning',
          iconColor: ColorsWIP.Yellow500,
          textColor: ColorsWIP.Yellow700,
        };
      case 'error':
        return {
          backgroundColor: ColorsWIP.Red50,
          borderColor: ColorsWIP.Red500,
          icon: 'error',
          iconColor: ColorsWIP.Red500,
          textColor: ColorsWIP.Red700,
        };
      case 'success':
        return {
          backgroundColor: ColorsWIP.Green50,
          borderColor: ColorsWIP.Green500,
          icon: 'done',
          iconColor: ColorsWIP.Green500,
          textColor: ColorsWIP.Green700,
        };
      case 'info':
      default:
        return {
          backgroundColor: ColorsWIP.Blue50,
          borderColor: ColorsWIP.Blue500,
          icon: 'info',
          iconColor: ColorsWIP.Blue500,
          textColor: ColorsWIP.Blue700,
        };
    }
  }, [intent]);

  return (
    <AlertContainer
      background={backgroundColor}
      $borderColor={borderColor}
      $textColor={textColor}
      padding={{horizontal: 16, vertical: 12}}
    >
      <Group direction="row" spacing={12} alignItems="flex-start">
        <IconWIP name={icon as IconName} color={iconColor} />
        <Group direction="column" spacing={8}>
          <AlertTitle>{title}</AlertTitle>
          {description ? <AlertDescription>{description}</AlertDescription> : null}
        </Group>
      </Group>
    </AlertContainer>
  );
};

Alert.defaultProps = {
  intent: 'info',
};

const AlertContainer = styled(Box)<{$borderColor: string; $textColor: string}>`
  box-shadow: inset 4px 0 ${({$borderColor}) => $borderColor};
  color: ${({$textColor}) => $textColor};

  a:link,
  a:visited,
  a:hover,
  a:active {
    color: ${({$textColor}) => $textColor};
    text-decoration: underline;
  }
`;

const AlertTitle = styled.div`
  font-weight: 600;
`;

const AlertDescription = styled.div`
  font-weight: 400;
`;
