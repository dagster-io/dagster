import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {ButtonLink} from '../ui/ButtonLink';
import {Checkbox} from '../ui/Checkbox';
import {ColorsWIP} from '../ui/Colors';
import {MetadataTable} from '../ui/MetadataTable';
import {PageHeader} from '../ui/PageHeader';
import {Heading, Subheading} from '../ui/Text';

import {FeatureFlag, getFeatureFlags, setFeatureFlags} from './Flags';
import {TimezoneSelect} from './time/TimezoneSelect';
import {automaticLabel} from './time/browserTimezone';

const SettingsRoot = () => {
  useDocumentTitle('User settings');

  const [flags, setFlags] = React.useState<FeatureFlag[]>(() => getFeatureFlags());

  React.useEffect(() => {
    setFeatureFlags(flags);
  });

  const toggleFlag = (flag: FeatureFlag) => {
    setFlags(flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag]);
    window.location.reload();
  };

  const trigger = React.useCallback(
    (timezone: string) => (
      <ButtonLink>{timezone === 'Automatic' ? automaticLabel() : timezone}</ButtonLink>
    ),
    [],
  );

  return (
    <div style={{height: '100vh', overflowY: 'auto'}}>
      <PageHeader title={<Heading>User settings</Heading>} />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Box padding={{bottom: 8}}>
          <Subheading>Preferences</Subheading>
        </Box>
        <MetadataTable
          rows={[
            {
              key: 'Timezone',
              value: <TimezoneSelect trigger={trigger} />,
            },
          ]}
        />
      </Box>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'top', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Box padding={{bottom: 8}}>
          <Subheading>Experimental features</Subheading>
        </Box>
        <MetadataTable
          rows={[
            {
              key: 'Debug console logging',
              value: (
                <Checkbox
                  format="switch"
                  checked={flags.includes(FeatureFlag.flagDebugConsoleLogging)}
                  onChange={() => toggleFlag(FeatureFlag.flagDebugConsoleLogging)}
                />
              ),
            },
            {
              key: 'Experimental Asset APIs',
              value: (
                <Checkbox
                  format="switch"
                  checked={flags.includes(FeatureFlag.flagAssetGraph)}
                  onChange={() => toggleFlag(FeatureFlag.flagAssetGraph)}
                />
              ),
            },
            {
              key: 'Live reload repositories',
              value: (
                <Checkbox
                  format="switch"
                  checked={flags.includes(FeatureFlag.flagLiveReload)}
                  onChange={() => toggleFlag(FeatureFlag.flagLiveReload)}
                />
              ),
            },
          ]}
        />
      </Box>
    </div>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default SettingsRoot;
