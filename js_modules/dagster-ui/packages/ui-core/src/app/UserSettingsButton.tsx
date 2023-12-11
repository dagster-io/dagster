import {
  IconWrapper,
  Icon,
  CoreColors,
  ProductTour,
  ProductTourPosition,
} from '@dagster-io/ui-components';
import {DAGSTER_THEME_KEY} from '@dagster-io/ui-components/src/theme/theme';
import Image from 'next/image';
import * as React from 'react';
import styled from 'styled-components';

import {useStateWithStorage} from '../hooks/useStateWithStorage';

import {UserSettingsDialog} from './UserSettingsDialog';
import {getVisibleFeatureFlagRows} from './getVisibleFeatureFlagRows';
import uiThemes from './ui-themes.jpg';

const SettingsButton = styled.button`
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 24px;

  ${IconWrapper} {
    transition: background 50ms linear;
  }

  &:hover ${IconWrapper} {
    background: ${CoreColors.White};
  }

  &:active ${IconWrapper} {
    background: ${CoreColors.White};
  }

  &:focus {
    outline: none;

    ${IconWrapper} {
      background: ${CoreColors.White};
    }
  }
`;

export const UserSettingsButton = () => {
  const [isOpen, setIsOpen] = React.useState(false);

  const [theme] = useStateWithStorage(DAGSTER_THEME_KEY, (value: any) => value);
  const [shouldHideUIThemeNux, setShouldHideUIThemeNux] = useStateWithStorage<string | null>(
    'dagster-theme-nux',
    (value) => value,
  );

  const button = (
    <SettingsButton onClick={() => setIsOpen(true)} title="User settings">
      <Icon name="settings" color={CoreColors.Gray200} />
    </SettingsButton>
  );

  const target =
    // If the user already has a theme setting, or has hidden the product tour already, just
    // show the usual gear button.
    !!theme || shouldHideUIThemeNux ? (
      button
    ) : (
      <ProductTour
        title="New: UI Themes"
        description={
          <span>You can now select a dark or light mode UI theme from your user settings.</span>
        }
        position={ProductTourPosition.BOTTOM_RIGHT}
        object={
          <div style={{borderRadius: 6, overflow: 'hidden'}}>
            <Image
              src={uiThemes}
              alt="UI Themes"
              width={230}
              height={130}
              style={{display: 'block'}}
            />
          </div>
        }
        actions={{
          dismiss: () => {
            setShouldHideUIThemeNux('1');
          },
        }}
        modifiers={{offset: {enabled: true, options: {offset: [-12, 8]}}}}
      >
        {button}
      </ProductTour>
    );

  return (
    <>
      {target}
      <UserSettingsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        visibleFlags={getVisibleFeatureFlagRows()}
      />
    </>
  );
};
