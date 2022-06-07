import {Button, DialogFooter, Dialog, Tooltip, Icon} from '@dagster-io/ui';
import * as React from 'react';

import {ConfigEditorWithSchema} from './ConfigEditorWithSchema';

interface Props {
  onConfigChange: (config: string) => void;
  onSave: () => void;
  onClose: () => void;
  config: string | undefined;
  configSchema: any | undefined;
  isLoading: boolean;
  saveText: string;
  identifier: string;
  title: string;
  isSubmitting: boolean;
  error?: string | null;
  isOpen: boolean;
}

export const ConfigEditorDialog: React.FC<Props> = ({
  config,
  configSchema,
  isLoading,
  isSubmitting,
  error,
  onSave,
  onClose,
  onConfigChange,
  identifier,
  title,
  saveText,
  isOpen,
}) => {
  return (
    <Dialog
      isOpen={isOpen}
      title={title}
      onClose={onClose}
      style={{maxWidth: '90%', minWidth: '70%', width: 1000}}
    >
      <ConfigEditorWithSchema
        onConfigChange={onConfigChange}
        config={config}
        configSchema={configSchema}
        isLoading={isLoading}
        identifier={identifier}
      />
      <DialogFooter topBorder>
        {error ? (
          <Tooltip
            isOpen={true}
            content={error}
            placement="bottom-start"
            modifiers={{offset: {enabled: true, options: {offset: [0, 16]}}}}
          >
            <Icon name="warning" />
          </Tooltip>
        ) : null}
        <Button intent="primary" onClick={onSave} disabled={isLoading || !!error || isSubmitting}>
          {saveText}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
