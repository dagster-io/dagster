import {Icon} from '@dagster-io/ui-components';
import {useState} from 'react';
import {useVisibleFeatureFlagRows} from 'shared/app/useVisibleFeatureFlagRows.oss';

import {TopNavButton} from './TopNavButton';
import {UserSettingsDialog} from './UserSettingsDialog/UserSettingsDialog';

export const UserSettingsButton = () => {
  const [isOpen, setIsOpen] = useState(false);
  const visibleFlags = useVisibleFeatureFlagRows();

  return (
    <>
      <TopNavButton onClick={() => setIsOpen(true)} title="User settings">
        <Icon name="settings" size={20} />
      </TopNavButton>
      <UserSettingsDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        visibleFlags={visibleFlags}
      />
    </>
  );
};
