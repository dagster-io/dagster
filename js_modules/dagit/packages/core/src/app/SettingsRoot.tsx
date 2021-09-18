import {Switch} from '@blueprintjs/core';
import * as React from 'react';

import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {ButtonLink} from '../ui/ButtonLink';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {Page} from '../ui/Page';
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
    <Page style={{height: '100vh', overflowY: 'auto'}}>
      <Group direction="column" spacing={24}>
        <PageHeader title={<Heading>User settings</Heading>} />
        <Group direction="column" spacing={16}>
          <Subheading>Preferences</Subheading>
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
                    checked={flags.includes(FeatureFlag.flagDebugConsoleLogging)}
                    onChange={() => toggleFlag(FeatureFlag.flagDebugConsoleLogging)}
                  />
                ),
              },
              {
                key: 'Experimental Core APIs (Job & Graph)',
                value: (
                  <Switch
                    checked={flags.includes(FeatureFlag.flagPipelineModeTuples)}
                    onChange={() => toggleFlag(FeatureFlag.flagPipelineModeTuples)}
                  />
                ),
              },
              {
                key: 'Experimental Asset APIs',
                value: (
                  <Switch
                    checked={flags.includes(FeatureFlag.flagAssetGraph)}
                    onChange={() => toggleFlag(FeatureFlag.flagAssetGraph)}
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

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default SettingsRoot;
