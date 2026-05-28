import {Box, Colors, TextInput} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useEffect, useMemo, useState} from 'react';
import * as yaml from 'yaml';

import styles from './css/CodeLocationComponentInstancesSubtab.module.css';

export type UIComponentEditorMode = 'add' | 'edit';

interface BaseProps {
  locationName: string;
  componentType: string;
  onChange: (state: UIComponentEditorState) => void;
}

interface AddProps extends BaseProps {
  mode: 'add';
  initialAttributes?: string;
}

interface EditProps extends BaseProps {
  mode: 'edit';
  componentId: string;
  initialAttributes: string;
}

export type UIComponentEditorBodyProps = AddProps | EditProps;

export interface UIComponentEditorState {
  componentId: string;
  attributes: string;
  isValid: boolean;
}

const isPlainObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

export const UIComponentEditorBody = (props: UIComponentEditorBodyProps) => {
  const {onChange} = props;
  const isEditMode = props.mode === 'edit';

  const [componentId, setComponentId] = useState<string>(() =>
    props.mode === 'edit' ? props.componentId : '',
  );
  const [yamlText, setYamlText] = useState<string>(() => props.initialAttributes ?? '');

  const yamlParseError = useMemo(() => {
    if (yamlText.trim() === '') {
      return null;
    }
    try {
      const parsed = yaml.parse(yamlText);
      if (parsed === null || parsed === undefined) {
        return null;
      }
      if (!isPlainObject(parsed)) {
        return 'Top-level YAML value must be a mapping (object).';
      }
      return null;
    } catch (e) {
      return e instanceof Error ? e.message : 'YAML parse error';
    }
  }, [yamlText]);

  const idIsValid = isEditMode || componentId.trim().length > 0;
  const isValid = yamlParseError === null && idIsValid;

  useEffect(() => {
    onChange({
      componentId: componentId.trim(),
      attributes: yamlText,
      isValid,
    });
  }, [componentId, yamlText, isValid, onChange]);

  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box flex={{direction: 'column', gap: 6}}>
        <span className={styles.fieldLabel}>Attributes</span>
        <Box border="all" className={styles.editorFrame}>
          <StyledRawCodeMirror
            value={yamlText}
            options={{
              mode: 'yaml',
              lineNumbers: true,
              readOnly: false,
            }}
            handlers={{
              onChange: (instance) => setYamlText(instance.getValue()),
            }}
          />
        </Box>
        {yamlParseError ? <span style={{color: Colors.textRed()}}>{yamlParseError}</span> : null}
      </Box>
      <Box flex={{direction: 'column', gap: 6}}>
        <span className={styles.fieldLabel}>Component ID</span>
        <TextInput
          value={componentId}
          onChange={(e) => setComponentId(e.target.value)}
          disabled={isEditMode}
          placeholder="my_component"
          fill
        />
      </Box>
    </Box>
  );
};
