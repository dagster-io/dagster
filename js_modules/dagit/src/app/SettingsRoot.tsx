import {Switch} from '@blueprintjs/core';
import * as React from 'react';

import {getFeatureFlags, setFeatureFlags, FeatureFlag} from 'src/app/Util';
import {TimezoneSelect} from 'src/app/time/TimezoneSelect';
import {automaticLabel} from 'src/app/time/browserTimezone';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading, Subheading} from 'src/ui/Text';

export const SettingsRoot = () => {
  useDocumentTitle('Settings');

  const [flags, setFlags] = React.useState<FeatureFlag[]>(() => getFeatureFlags());

  const toggleFlag = (flag: FeatureFlag) => {
    const updated = flags.includes(flag) ? flags.filter((f) => f !== flag) : [...flags, flag];
    setFeatureFlags(updated);
    setFlags(updated);
  };

  const trigger = React.useCallback(
    (timezone: string) => (
      <ButtonLink>{timezone === 'Automatic' ? automaticLabel() : timezone}</ButtonLink>
    ),
    [],
  );

  return (
    <Page style={{height: '100vh', overflowY: 'auto'}}>
      <Group direction="column" spacing={24}>
        <PageHeader title={<Heading>Settings</Heading>} />
        <Group direction="column" spacing={16}>
          <Subheading>User preferences</Subheading>
          <MetadataTable
            rows={[
              {
                key: 'Timezone',
                value: <TimezoneSelect trigger={trigger} />,
              },
            ]}
          />
        </Group>
        <Group direction="column" spacing={16}>
          <Subheading>Experimental features</Subheading>
          <MetadataTable
            rows={[
              {
                key: 'Debug console logging',
                value: (
                  <Switch
                    checked={flags.includes(FeatureFlag.DebugConsoleLogging)}
                    onChange={() => toggleFlag(FeatureFlag.DebugConsoleLogging)}
                  />
                ),
              },
              {
                key: 'Simplified left nav',
                value: (
                  <Switch
                    checked={flags.includes(FeatureFlag.LeftNav)}
                    onChange={() => {
                      toggleFlag(FeatureFlag.LeftNav);
                      window.location.reload();
                    }}
                  />
                ),
              },
            ]}
          />
        </Group>
      </Group>
    </Page>
  );
};
