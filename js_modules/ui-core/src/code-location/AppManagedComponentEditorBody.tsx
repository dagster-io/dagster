import {Box, Colors, Tab, Tabs, TextInput} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useCallback, useEffect, useMemo, useState} from 'react';
import * as yaml from 'yaml';

import {useQuery} from '../apollo-client';
import {CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY} from './CodeLocationAppManagedComponentsQuery';
import {ComponentSchemaForm} from './component-form';
import {isFormDataValid} from './component-form/validate';
import styles from './css/CodeLocationComponentInstancesSubtab.module.css';
import {
  CodeLocationAppManagedComponentsQuery,
  CodeLocationAppManagedComponentsQueryVariables,
} from './types/CodeLocationAppManagedComponentsQuery.types';

// JSON Schema marker emitted by ``ComponentFormConfig(id_source=True)`` on the
// Python side — flags a single field whose value should be interpolated into
// the auto-generated component id (e.g. ``MyComponent[<field value>]``).
const APP_ID_SOURCE = 'x-app-id-source';

export type AppManagedComponentEditorMode = 'add' | 'edit';
type EditorView = 'form' | 'yaml';

interface FormSchema {
  dataSchema: unknown;
  uiSchema: unknown;
}

interface BaseProps {
  isActive: boolean;
  locationName: string;
  componentType: string;
  // The component's schema, pre-split into the (dataSchema, uiSchema) pair RJSF
  // expects. Computed server-side; null when the component declares no model.
  formSchema?: FormSchema | null;
  onChange: (state: AppManagedComponentEditorState) => void;
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

export type AppManagedComponentEditorBodyProps = AddProps | EditProps;

export interface AppManagedComponentEditorState {
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

export const AppManagedComponentEditorBody = (props: AppManagedComponentEditorBodyProps) => {
  const {isActive, locationName, componentType, formSchema, onChange} = props;
  const isEditMode = props.mode === 'edit';
  const dataSchema = isPlainObject(formSchema?.dataSchema) ? formSchema.dataSchema : null;
  const uiSchema = isPlainObject(formSchema?.uiSchema) ? formSchema.uiSchema : {};

  // Leaf class drives auto-generated ids. ``componentType`` is dotted (e.g.
  // "dagster.EchoComponent").
  const classLeaf = useMemo(() => {
    const parts = componentType.split('.');
    return parts[parts.length - 1] || componentType;
  }, [componentType]);

  // Optional ``id_source`` field marked via ComponentFormConfig. The
  // ``x-app-id-source`` marker is an ``x-app-*`` key (not a ``ui:`` rendering
  // hint), so ``split_form_schema`` leaves it on the property in ``dataSchema``.
  const idSourceField = useMemo<string | null>(() => {
    if (!dataSchema) {
      return null;
    }
    const properties = (dataSchema as {properties?: Record<string, unknown>}).properties;
    if (!properties) {
      return null;
    }
    return (
      Object.entries(properties).find(
        ([, propSchema]) => isPlainObject(propSchema) && propSchema[APP_ID_SOURCE] === true,
      )?.[0] ?? null
    );
  }, [dataSchema]);

  // Existing ids — used for the integer-suffix dedup in Add mode only.
  const {data: existingComponentsData} = useQuery<
    CodeLocationAppManagedComponentsQuery,
    CodeLocationAppManagedComponentsQueryVariables
  >(CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY, {
    variables: {locationName},
    skip: isEditMode || !isActive,
  });

  const existingIds = useMemo<Set<string>>(() => {
    const result = existingComponentsData?.appManagedComponentsForLocationOrError;
    if (result?.__typename !== 'AppManagedComponents') {
      return new Set();
    }
    return new Set(result.components.map((c) => c.componentId));
  }, [existingComponentsData]);

  // With a schema, ``formValues`` is the single source of truth and the YAML
  // tab is a read-only preview derived from it. Without a schema there is no
  // form, so the YAML editor is editable and ``yamlText`` is the source of
  // truth instead.
  const [componentId, setComponentId] = useState<string>(() =>
    props.mode === 'edit' ? props.componentId : '',
  );
  const [view, setView] = useState<EditorView>(dataSchema ? 'form' : 'yaml');
  const [formValues, setFormValues] = useState<Record<string, any>>(() =>
    parseYamlObject(props.initialAttributes ?? ''),
  );
  // Seed validity from the initial form data rather than assuming valid: RJSF
  // only reports validity through ``onChange``, which never fires on mount, so
  // an untouched form with unfilled required fields would otherwise read as
  // valid and enable submit. With no schema, validity is driven by the YAML
  // path instead (see ``isValid`` below), so default to true.
  const [formIsValid, setFormIsValid] = useState<boolean>(() =>
    dataSchema ? isFormDataValid(dataSchema, parseYamlObject(props.initialAttributes ?? '')) : true,
  );
  const [yamlText, setYamlText] = useState<string>(() =>
    dataSchema ? '' : (props.initialAttributes ?? ''),
  );

  const autoGeneratedId = useMemo<string>(() => {
    if (idSourceField) {
      const raw = formValues[idSourceField];
      if (raw !== undefined && raw !== null && raw !== '') {
        const candidate = `${classLeaf}[${String(raw)}]`;
        // Fall through to the integer-suffix path if the id_source value
        // would collide with an existing component.
        if (!existingIds.has(candidate)) {
          return candidate;
        }
      }
    }
    let n = 1;
    while (existingIds.has(`${classLeaf}[${n}]`)) {
      n++;
    }
    return `${classLeaf}[${n}]`;
  }, [classLeaf, idSourceField, formValues, existingIds]);

  useEffect(() => {
    if (isEditMode || !isActive) {
      return;
    }
    setComponentId(autoGeneratedId);
  }, [autoGeneratedId, isEditMode, isActive]);

  const handleFormChange = useCallback((next: Record<string, any>, isValid: boolean) => {
    setFormValues(next);
    setFormIsValid(isValid);
  }, []);

  // YAML rendered in the YAML view (and submitted on save). With a schema
  // this is derived live from the form, so the two stay in sync without any
  // user-driven conversion. Without a schema it's just the editable buffer.
  const attributes = useMemo<string>(
    () => (dataSchema ? serializeFormValues(formValues) : yamlText),
    [dataSchema, formValues, yamlText],
  );

  // Only meaningful when the user can type YAML directly — i.e. when there is
  // no schema. With a schema the YAML pane is derived and always valid.
  const yamlParseError = useMemo(() => {
    if (dataSchema || yamlText.trim() === '') {
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
  }, [dataSchema, yamlText]);

  const idIsValid = isEditMode || componentId.trim().length > 0;
  const isValid = yamlParseError === null && (!dataSchema || formIsValid) && idIsValid;

  // Surface state to the host dialog so its Save button can act on it.
  useEffect(() => {
    onChange({
      componentId: componentId.trim(),
      attributes,
      isValid,
    });
  }, [componentId, attributes, isValid, onChange]);

  return (
    <Box flex={{direction: 'column', gap: 16}}>
      <Box flex={{direction: 'column', gap: 6}}>
        <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          <span className={styles.fieldLabel}>Attributes</span>
          {dataSchema ? (
            <Tabs selectedTabId={view} onChange={(id) => setView(id as EditorView)}>
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
              value={attributes}
              options={{
                mode: 'yaml',
                lineNumbers: true,
                readOnly: dataSchema !== null,
              }}
              handlers={{
                onChange: (instance) => {
                  if (!dataSchema) {
                    setYamlText(instance.getValue());
                  }
                },
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
        <TextInput value={componentId} disabled placeholder="my_component" fill />
      </Box>
    </Box>
  );
};
