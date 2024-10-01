import {SettingsLayout} from './SettingsLayout';
import {SettingsLeftPane} from './SettingsLeftPane';
import {SettingsMainPane} from './SettingsMainPane';

export const SettingsRoot = () => {
  return <SettingsLayout left={<SettingsLeftPane />} main={<SettingsMainPane />} />;
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default SettingsRoot;
