import {SettingsLayout} from './SettingsLayout';
import {SettingsMainPane} from './SettingsMainPane';
import {SettingsTabs} from './SettingsTabs';

export const SettingsRoot = () => {
  return <SettingsLayout tabs={<SettingsTabs />} main={<SettingsMainPane />} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default SettingsRoot;
