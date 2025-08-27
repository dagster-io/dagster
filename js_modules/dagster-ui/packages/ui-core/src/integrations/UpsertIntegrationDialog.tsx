import {
  Alert,
  Box,
  Button,
  ButtonGroup,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  DialogHeader,
  FontFamily,
  Icon,
  TextArea,
  TextInput,
} from '@dagster-io/ui-components';
import snakeCase from 'lodash/snakeCase';
import React, {useState} from 'react';

import {IntegrationMarkdownContent} from './IntegrationMarkdownContent';
import {IntegrationTag, IntegrationTagIcon, IntegrationTagLabel} from './IntegrationTag';
import {IntegrationTopcard} from './IntegrationTopcard';
import {IntegrationConfig, IntegrationFrontmatter} from './types';

const INPUT_WIDTH = 376;

export const UpsertIntegrationDialog = ({
  isOpen,
  initial,
  title,
  isNew,
  onSave,
  onDelete,
  onCancel,
}: {
  isOpen: boolean;
  isNew: boolean;
  title: string;
  initial: IntegrationConfig;
  onSave: (updated: IntegrationConfig) => Promise<void>;
  onCancel: () => void;
  onDelete?: () => Promise<void>;
}) => {
  const [config, setConfig] = useState<IntegrationConfig>(initial);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [textmode, setTextmode] = useState<'md' | 'preview'>('md');

  const onChangeFrontmatter = (updates: Partial<IntegrationFrontmatter>) =>
    setConfig({...config, frontmatter: {...config.frontmatter, ...updates}});

  React.useEffect(() => {
    if (!isOpen) {
      setConfig(initial);
    }
  }, [initial, isOpen]);

  return (
    <Dialog isOpen={isOpen} style={{width: '90vw', maxWidth: 1000}}>
      <DialogHeader icon="compute_kind" label={title} />
      <DialogBody>
        {isNew && (
          <Box padding={{bottom: 24}}>
            <Alert
              intent="info"
              title="Private and organization-scoped"
              description="Document a python module that defines components to your teams Integrations Marketplace to make it discoverable and easy to use."
            />
          </Box>
        )}
        <Box flex={{direction: 'row', gap: 24}}>
          <Box style={{flex: 1}} flex={{direction: 'column', gap: 16}}>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="name-input">Name*</label>
              <TextInput
                id="name-input"
                aria-label="name"
                value={config.frontmatter.name}
                onChange={(e) =>
                  onChangeFrontmatter({
                    name: e.target.value,
                    id: isNew ? snakeCase(e.target.value) : config.frontmatter.id,
                  })
                }
                required
                placeholder="Marketing Service"
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="description-input">Description*</label>
              <TextInput
                id="description-input"
                aria-label="description"
                value={config.frontmatter.description}
                onChange={(e) => onChangeFrontmatter({description: e.target.value})}
                placeholder="Description"
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="installationCommand-input">Installation Command*</label>
              <TextInput
                id="installationCommand-input"
                aria-label="installationCommand"
                value={config.frontmatter.installationCommand ?? ''}
                onChange={(e) => onChangeFrontmatter({installationCommand: e.target.value})}
                placeholder="curl -O https://myname:mypass@example.com/pypi/packages/my-package-1.0.0.tar.gz && pip install ./my-package-1.0.0.tar.gz"
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="icon-input">Logo URL (or Logo Emoji)</label>
              <TextInput
                id="icon-input"
                aria-label="icon"
                maxLength={2}
                value={config.frontmatter.logo ?? ''}
                onChange={(e) => onChangeFrontmatter({logo: e.target.value || null})}
                placeholder="AB"
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="partnerlink-input">Documentation Link</label>
              <TextInput
                id="partnerlink-input"
                aria-label="partnerlink"
                value={config.frontmatter.partnerlink ?? ''}
                onChange={(e) => onChangeFrontmatter({partnerlink: e.target.value})}
                placeholder=""
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="source-input">Source Repository Link</label>
              <TextInput
                id="source-input"
                aria-label="source"
                value={config.frontmatter.source ?? ''}
                onChange={(e) => onChangeFrontmatter({source: e.target.value})}
                placeholder=""
                style={{width: INPUT_WIDTH}}
              />
            </Box>
            <Box flex={{direction: 'column', gap: 8}} style={{width: '100%'}}>
              <label htmlFor="source-input">Tags</label>
              <Box flex={{gap: 4, wrap: 'wrap'}}>
                {Object.values(IntegrationTag)
                  .filter(
                    (t) =>
                      t !== IntegrationTag.CommunitySupported &&
                      t !== IntegrationTag.DagsterSupported,
                  )
                  .map((tag) => (
                    <Button
                      key={tag}
                      icon={<Icon name={IntegrationTagIcon[tag]} />}
                      onClick={() =>
                        onChangeFrontmatter({
                          tags: config.frontmatter.tags.includes(tag)
                            ? config.frontmatter.tags.filter((f) => f !== tag)
                            : [...config.frontmatter.tags, tag],
                        })
                      }
                      style={{
                        lineHeight: '1rem',
                        backgroundColor: config.frontmatter.tags.includes(tag)
                          ? Colors.backgroundBlue()
                          : 'transparent',
                      }}
                    >
                      {IntegrationTagLabel[tag]}
                    </Button>
                  ))}
              </Box>
            </Box>
          </Box>
          <Box
            style={{flex: 2, height: 500, minWidth: 0}}
            flex={{direction: 'column', alignItems: 'flex-end', gap: 12}}
          >
            <ButtonGroup
              activeItems={new Set([textmode])}
              onClick={setTextmode}
              buttons={[
                {id: 'md', label: 'Markdown', icon: 'console'},
                {id: 'preview', label: 'Preview', icon: 'search'},
              ]}
            />
            <div style={{flex: 1, width: '100%', minWidth: 0, minHeight: 0}}>
              {textmode === 'md' ? (
                <TextArea
                  $resize="none"
                  style={{width: '100%', height: '100%', fontFamily: FontFamily.monospace}}
                  value={config.content}
                  onChange={(e) => setConfig({...config, content: e.target.value})}
                />
              ) : (
                <Box
                  border="all"
                  padding={8}
                  background={Colors.backgroundLight()}
                  style={{width: '100%', height: '100%', overflow: 'auto'}}
                >
                  <IntegrationTopcard integration={config.frontmatter} />
                  <IntegrationMarkdownContent integration={config} />
                </Box>
              )}
            </div>
          </Box>
        </Box>
      </DialogBody>
      <DialogFooter
        left={
          onDelete && (
            <Button
              intent="danger"
              icon={<Icon name="trash" />}
              loading={deleting}
              onClick={async () => {
                setDeleting(true);
                await onDelete();
                setDeleting(false);
              }}
            >
              Delete
            </Button>
          )
        }
      >
        <Button onClick={onCancel}>Cancel</Button>
        <Button
          disabled={
            !config.frontmatter.name ||
            !config.frontmatter.description ||
            !config.frontmatter.installationCommand
          }
          intent="primary"
          loading={saving}
          onClick={async () => {
            setSaving(true);
            await onSave(config);
            setSaving(false);
          }}
        >
          Done
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
