import * as React from 'react';
import styled from 'styled-components';

import {Box} from './Box';
import {Colors} from './Color';
import {Group} from './Group';
import {Icon, IconName} from './Icon';

export type AlertIntent = 'info' | 'warning' | 'error' | 'success';

interface Props {
  intent?: AlertIntent;
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  onClose?: () => void;
}

export const Alert = (props: Props) => {
  const {intent = 'info', title, description, onClose} = props;

  const {backgroundColor, borderColor, icon, iconColor, textColor} = React.useMemo(() => {
    switch (intent) {
      case 'warning':
        return {
          backgroundColor: Colors.backgroundYellow(),
          borderColor: Colors.accentYellow(),
          icon: 'warning',
          iconColor: Colors.accentYellow(),
          textColor: Colors.textYellow(),
        };
      case 'error':
        return {
          backgroundColor: Colors.backgroundRed(),
          borderColor: Colors.accentRed(),
          icon: 'error',
          iconColor: Colors.accentRed(),
          textColor: Colors.textRed(),
        };
      case 'success':
        return {
          backgroundColor: Colors.backgroundGreen(),
          borderColor: Colors.accentGreen(),
          icon: 'done',
          iconColor: Colors.accentGreen(),
          textColor: Colors.textGreen(),
        };
      case 'info':
      default:
        return {
          backgroundColor: Colors.backgroundBlue(),
          borderColor: Colors.accentBlue(),
          icon: 'info',
          iconColor: Colors.accentBlue(),
          textColor: Colors.textBlue(),
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
          {props.icon || <Icon name={icon as IconName} color={iconColor} />}
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
