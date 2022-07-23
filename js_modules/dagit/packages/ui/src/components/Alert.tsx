import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
import {Colors} from './Colors';
import {Group} from './Group';
import {IconName, Icon} from './Icon';

export type AlertIntent = 'info' | 'warning' | 'error' | 'success';

interface Props {
  intent: AlertIntent;
  title: React.ReactNode;
  description?: React.ReactNode;
  onClose?: () => void;
}

export const Alert: React.FC<Props> = (props) => {
  const {intent, title, description, onClose} = props;

  const {backgroundColor, borderColor, icon, iconColor, textColor} = React.useMemo(() => {
    switch (intent) {
      case 'warning':
        return {
          backgroundColor: Colors.Yellow50,
          borderColor: Colors.Yellow500,
          icon: 'warning',
          iconColor: Colors.Yellow500,
          textColor: Colors.Yellow700,
        };
      case 'error':
        return {
          backgroundColor: Colors.Red50,
          borderColor: Colors.Red500,
          icon: 'error',
          iconColor: Colors.Red500,
          textColor: Colors.Red700,
        };
      case 'success':
        return {
          backgroundColor: Colors.Green50,
          borderColor: Colors.Green500,
          icon: 'done',
          iconColor: Colors.Green500,
          textColor: Colors.Green700,
        };
      case 'info':
      default:
        return {
          backgroundColor: Colors.Blue50,
          borderColor: Colors.Blue500,
          icon: 'info',
          iconColor: Colors.Blue500,
          textColor: Colors.Blue700,
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
      <Box flex={{direction: 'row', justifyContent: 'space-between'}}>
        <Group direction="row" spacing={12} alignItems="flex-start">
          <Icon name={icon as IconName} color={iconColor} />
          <Group direction="column" spacing={8}>
            <AlertTitle>{title}</AlertTitle>
            {description ? <AlertDescription>{description}</AlertDescription> : null}
          </Group>
        </Group>
        {!!onClose ? (
          <ButtonWrapper onClick={onClose}>
            <Icon name="close" color={textColor} />
          </ButtonWrapper>
        ) : null}
      </Box>
    </AlertContainer>
  );
};

Alert.defaultProps = {
  intent: 'info',
};

const ButtonWrapper = styled.button`
  background: none;
  color: inherit;
  border: none;
  padding: 0;
  font: inherit;
  cursor: pointer;
  flex-direction: column;
  height: fit-content;
`;

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
