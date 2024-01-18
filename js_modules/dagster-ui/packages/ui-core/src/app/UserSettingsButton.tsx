import * as React from 'react';
import styled from 'styled-components';

import {
  Icon,
  IconWrapper,
  colorNavTextHover,
  colorNavTextSelected,
} from '@dagster-io/ui-components';

import {UserSettingsDialog} from './UserSettingsDialog';
import {getVisibleFeatureFlagRows} from './getVisibleFeatureFlagRows';

const SettingsButton = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 24px;

  ${IconWrapper} {
    transition: background 50ms linear;
  }

  &:hover ${IconWrapper} {
    background: ${colorNavTextHover()};
  }

  &:active ${IconWrapper} {
    background: ${colorNavTextHover()};
  }

  &:focus {
    outline: none;

    ${IconWrapper} {
      background: ${colorNavTextHover()};
    }
  }
`;

export const UserSettingsButton = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  return (
    <>
      <SettingsButton onClick={() => setIsOpen(true)} title="User settings">
        <Icon name="settings" color={colorNavTextSelected()} />
      </SettingsButton>
      <UserSettingsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        visibleFlags={getVisibleFeatureFlagRows()}
      />
    </>
  );
};
