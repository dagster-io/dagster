import {Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';
import {IntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {UpsertIntegrationDialog} from './UpsertIntegrationDialog';
import {IntegrationConfig} from './types';

interface Props {
  provider: IntegrationsProvider;
}

const INITIAL_PRIVATE_INTEGRATION: IntegrationConfig = {
  frontmatter: {
    id: '',
    name: '',
    title: '',
    description: '',
    logo: null,
    logoFilename: null,
    installationCommand: null,
    pypi: null,
    partnerlink: '',
    isPrivate: true,
    source: '',
    tags: [],
  },
  content: `
## Examples

\`\`\`
foo
\`\`\`

## Getting Started

...
`,
};

export const AddIntegrationButton = ({provider}: Props) => {
  const [isOpen, setOpen] = useState(false);

  if (!provider.addPrivateIntegrationDetails) {
    return null;
  }

  return (
    <>
      <UpsertIntegrationDialog
        isNew
        isOpen={isOpen}
        title="Add Private Integration"
        initial={INITIAL_PRIVATE_INTEGRATION}
        onCancel={() => setOpen(false)}
        onSave={async (created) => {
          await provider.addPrivateIntegrationDetails?.(created);
          setOpen(false);
        }}
      />

      {provider.canManageIntegrations === true ? (
        <Button icon={<Icon name="edit" />} onClick={() => setOpen(true)}>
          Add Private Integration
        </Button>
      ) : provider.canManageIntegrations === false ? (
        <Tooltip content="You do not have permission to manage organization settings.">
          <Button icon={<Icon name="edit" />} disabled>
            Add Private Integration
          </Button>
        </Tooltip>
      ) : /** oss */
      null}
    </>
  );
};
