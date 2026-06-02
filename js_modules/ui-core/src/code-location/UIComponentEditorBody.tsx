import {Box, Colors, Tab, Tabs, TextInput} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useCallback, useEffect, useMemo, useState} from 'react';
import * as yaml from 'yaml';

import {ComponentSchemaForm} from './component-form';
import styles from './css/CodeLocationComponentInstancesSubtab.module.css';

export type UIComponentEditorMode = 'add' | 'edit';
type EditorView = 'form' | 'yaml';

interface FormSchema {
  dataSchema: unknown;
  uiSchema: unknown;
}

interface BaseProps {
  locationName: string;
  componentType: string;
  // The component's schema, pre-split into the (dataSchema, uiSchema) pair RJSF
  // expects. Computed server-side; null when the component declares no model.
  formSchema?: FormSchema | null;
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

const isPlainObject = (v: unknown): v is Record<string, any> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

const parseYamlObject = (text: string): Record<string, any> => {
  if (text.trim() === '') {
    return {};
  }
  try {
    const parsed = yaml.parse(text);
    return isPlainObject(parsed) ? parsed : {};
  } catch {
    return {};
  }
};

const serializeFormValues = (values: Record<string, any>): string => {
  if (!values || Object.keys(values).length === 0) {
    return '';
  }
  return yaml.stringify(values);
};

export const UIComponentEditorBody = (props: UIComponentEditorBodyProps) => {
  const {formSchema, onChange} = props;
  const isEditMode = props.mode === 'edit';
  const dataSchema = isPlainObject(formSchema?.dataSchema) ? formSchema.dataSchema : null;
  const uiSchema = isPlainObject(formSchema?.uiSchema) ? formSchema.uiSchema : {};

  const [componentId, setComponentId] = useState<string>(() =>
    props.mode === 'edit' ? props.componentId : '',
  );
  const [view, setView] = useState<EditorView>(dataSchema ? 'form' : 'yaml');
  const [formValues, setFormValues] = useState<Record<string, any>>(() =>
    parseYamlObject(props.initialAttributes ?? ''),
  );
  const [formIsValid, setFormIsValid] = useState<boolean>(true);
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

  const handleSelectTab = useCallback(
    (next: EditorView) => {
      if (view === 'form' && next === 'yaml') {
        setYamlText(serializeFormValues(formValues));
      }
      setView(next);
    },
    [view, formValues],
  );

  const handleFormChange = useCallback((next: Record<string, any>, isValid: boolean) => {
    setFormValues(next);
    setFormIsValid(isValid);
  }, []);

  const attributesToSubmit = useMemo<string>(() => {
    if (view === 'form') {
      return serializeFormValues(formValues);
    }
    return yamlText;
  }, [view, formValues, yamlText]);

  const idIsValid = isEditMode || componentId.trim().length > 0;
  const yamlIsValid = yamlParseError === null;
  // Validate against whichever editor is active: the form's values in form view,
  // the serialized YAML text in YAML view. yamlText is only re-synced when
  // switching to YAML view, so it's stale while editing the form.
  const isValid = (view === 'form' ? formIsValid : yamlIsValid) && idIsValid;

  useEffect(() => {
    onChange({
      componentId: componentId.trim(),
      attributes: attributesToSubmit,
      isValid,
    });
  }, [componentId, attributesToSubmit, isValid, onChange]);

  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box flex={{direction: 'column', gap: 6}}>
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          <span className={styles.fieldLabel}>Attributes</span>
          {dataSchema ? (
            <Tabs selectedTabId={view} onChange={(id) => handleSelectTab(id as EditorView)}>
              <Tab id="form" title="Form" />
              <Tab id="yaml" title="YAML" />
            </Tabs>
          ) : null}
        </Box>
        {view === 'form' && dataSchema ? (
          <Box border="all" className={styles.formEditorFrame}>
            <ComponentSchemaForm
              dataSchema={dataSchema}
              uiSchema={uiSchema}
              formData={formValues}
              onChange={handleFormChange}
            />
          </Box>
        ) : (
          <Box border="all" className={styles.editorFrame}>
            <StyledRawCodeMirror
              value={yamlText}
              options={{
                mode: 'yaml',
                lineNumbers: true,
                readOnly: dataSchema !== null,
              }}
              handlers={{
                onChange: (instance) => setYamlText(instance.getValue()),
              }}
            />
          </Box>
        )}
        {view === 'yaml' && yamlParseError ? (
          <span style={{color: Colors.textRed()}}>{yamlParseError}</span>
        ) : null}
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
