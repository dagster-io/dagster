import {Body2, Box, Button, Icon, Tooltip} from '@dagster-io/ui-components';
import {useState} from 'react';
import {useHistory} from 'react-router-dom';
import {IntegrationsProvider} from 'shared/integrations/useIntegrationsProvider.oss';

import {IntegrationMarkdownContent} from './IntegrationMarkdownContent';
import {IntegrationTopcard} from './IntegrationTopcard';
import {UpsertIntegrationDialog} from './UpsertIntegrationDialog';
import styles from './css/SingleIntegrationPage.module.css';
import {IntegrationConfig} from './types';
import {useDOMTableOfContents} from './useDOMTableOfContents';

interface Props {
  integration: IntegrationConfig;
  provider: IntegrationsProvider;
}

export const SingleIntegrationPage = ({integration, provider}: Props) => {
  const {frontmatter} = integration;
  const {markdownRef, tableOfContents} = useDOMTableOfContents();
  const history = useHistory();

  const [isEditing, setEditing] = useState(false);

  return (
    <Box padding={{vertical: 24}} flex={{gap: 48, alignItems: 'flex-start'}}>
      <Box flex={{direction: 'column', gap: 12}} style={{minWidth: 600}}>
        <IntegrationTopcard integration={frontmatter}>
          {integration.frontmatter.isPrivate && (
            <>
              {provider.updatePrivateIntegrationDetails && (
                <UpsertIntegrationDialog
                  isOpen={isEditing}
                  isNew={false}
                  title="Edit Private Integration"
                  initial={integration}
                  onCancel={() => setEditing(false)}
                  onSave={async (updated) => {
                    await provider.updatePrivateIntegrationDetails?.(updated);
                    setEditing(false);
                  }}
                  onDelete={async () => {
                    await provider.deletePrivateIntegrationDetails?.(integration);
                    history.replace('/integrations');
                  }}
                />
              )}

              {provider?.canManageIntegrations !== undefined ? (
                <Tooltip
                  canShow={!provider.canManageIntegrations}
                  content="You do not have permission to manage organization settings."
                >
                  <Button
                    icon={<Icon name="edit" />}
                    disabled={!provider.canManageIntegrations}
                    onClick={() => setEditing(true)}
                  >
                    Edit
                  </Button>
                </Tooltip>
              ) : /** oss */
              null}
            </>
          )}
        </IntegrationTopcard>

        <div
          className={styles.markdownOutput}
          ref={(ref) => {
            markdownRef.current = ref;
          }}
        >
          <IntegrationMarkdownContent
            integration={integration}
            className={styles.integrationPage}
          />
        </div>
      </Box>
      <Box
        border="left"
        padding={{left: 24, vertical: 4}}
        style={{
          minWidth: '15vw',
          position: 'sticky',
          overflowY: 'auto',
          overflowX: 'hidden',
          maxHeight: 'calc(100vh - 148px)',
          top: 24,
        }}
      >
        {tableOfContents.map((heading, idx) => (
          <a href={`#${heading.id}`} key={`${heading.id}-${idx}`}>
            <div style={{paddingLeft: (heading.level - 1) * 12, paddingBottom: 4}}>
              <Body2>{heading.label}</Body2>
            </div>
          </a>
        ))}
      </Box>
    </Box>
  );
};
