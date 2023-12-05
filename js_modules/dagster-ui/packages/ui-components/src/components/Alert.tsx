import * as React from 'react';
import styled from 'styled-components';

import {
  colorAccentBlue,
  colorAccentGreen,
  colorAccentRed,
  colorAccentYellow,
  colorBackgroundBlue,
  colorBackgroundGreen,
  colorBackgroundRed,
  colorBackgroundYellow,
  colorTextBlue,
  colorTextGreen,
  colorTextRed,
  colorTextYellow,
} from '../theme/color';

import {Box} from './Box';
import {Group} from './Group';
import {IconName, Icon} from './Icon';

export type AlertIntent = 'info' | 'warning' | 'error' | 'success';

interface Props {
  intent: AlertIntent;
  title: React.ReactNode;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  onClose?: () => void;
}

export const Alert = (props: Props) => {
  const {intent, title, description, onClose} = props;

  const {backgroundColor, borderColor, icon, iconColor, textColor} = React.useMemo(() => {
    switch (intent) {
      case 'warning':
        return {
          backgroundColor: colorBackgroundYellow(),
          borderColor: colorAccentYellow(),
          icon: 'warning',
          iconColor: colorAccentYellow(),
          textColor: colorTextYellow(),
        };
      case 'error':
        return {
          backgroundColor: colorBackgroundRed(),
          borderColor: colorAccentRed(),
          icon: 'error',
          iconColor: colorAccentRed(),
          textColor: colorTextRed(),
        };
      case 'success':
        return {
          backgroundColor: colorBackgroundGreen(),
          borderColor: colorAccentGreen(),
          icon: 'done',
          iconColor: colorAccentGreen(),
          textColor: colorTextGreen(),
        };
      case 'info':
      default:
        return {
          backgroundColor: colorBackgroundBlue(),
          borderColor: colorAccentBlue(),
          icon: 'info',
          iconColor: colorAccentBlue(),
          textColor: colorTextBlue(),
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
