import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  NonIdealState,
  SpinnerWithText,
  Tag,
  Text,
  TextInput,
  showToast,
} from '@dagster-io/ui-components';
import {useCallback, useEffect, useMemo, useState} from 'react';

import {useMutation, useQuery} from '../apollo-client';
import {
  AppManagedComponentEditorBody,
  AppManagedComponentEditorState,
} from './AppManagedComponentEditorBody';
import {
  CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY,
  SET_APP_MANAGED_COMPONENT_MUTATION,
} from './CodeLocationAppManagedComponentsQuery';
import {CODE_LOCATION_COMPONENT_TYPES_QUERY} from './CodeLocationComponentTypesQuery';
import {AppManagedComponentMutationContext} from './appManagedComponentMutationContext';
import styles from './css/AppManagedComponentTypePickerDialog.module.css';
import {
  SetAppManagedComponentMutation,
  SetAppManagedComponentMutationVariables,
} from './types/CodeLocationAppManagedComponentsQuery.types';
import {
  CodeLocationComponentTypesQuery,
  CodeLocationComponentTypesQueryVariables,
} from './types/CodeLocationComponentTypesQuery.types';
import {COMMON_COLLATOR} from '../app/Util';

export interface AppManagedComponentEditTarget {
  componentId: string;
  componentType: string;
  attributes: string;
}

interface CommonProps {
  isOpen: boolean;
  onClose: () => void;
  /** Fires when a mutation returned PythonError. Parent surfaces this as the revert banner. */
  onFailed: (ctx: AppManagedComponentMutationContext, errorMessage: string) => void;
  locationName: string;
}

interface AddProps extends CommonProps {
  mode?: 'add';
  editTarget?: undefined;
  onCreated: (ctx: AppManagedComponentMutationContext) => void;
  onSaved?: undefined;
}

interface EditProps extends CommonProps {
  mode: 'edit';
  editTarget: AppManagedComponentEditTarget;
  onCreated?: undefined;
  onSaved: (ctx: AppManagedComponentMutationContext) => void;
}

type Props = AddProps | EditProps;

interface PickableType {
  name: string;
  namespace: string;
  description: string | null | undefined;
  formSchema: {dataSchema: unknown; uiSchema: unknown} | null | undefined;
}

// Match the catalog's ``descriptionStyle="truncated"`` behavior: render only
// the first non-empty paragraph of the (markdown) description.
const firstParagraph = (md: string | null | undefined) =>
  (md ?? '')
    .split('\n\n')
    .map((p) => p.trim())
    .find((p) => p.length > 0) ?? '';

// Source pill text — the namespace's top-level segment.
const sourceLabel = (namespace: string) => namespace.split('.')[0] || namespace;

export const AppManagedComponentTypePickerDialog = (props: Props) => {
  const isEdit = props.mode === 'edit';
  return (
    <Dialog
      isOpen={props.isOpen}
      onClose={props.onClose}
      title={isEdit ? 'Edit component instance' : 'Add component instance'}
      icon={isEdit ? 'edit' : 'add_circle'}
      style={{maxWidth: '90%', width: 720}}
    >
      {props.isOpen ? <AppManagedComponentTypePickerDialogBody {...props} /> : null}
    </Dialog>
  );
};

const AppManagedComponentTypePickerDialogBody = (props: Props) => {
  const {onClose, onFailed, locationName} = props;
  const isEdit = props.mode === 'edit';

  const typesQ = useQuery<
    CodeLocationComponentTypesQuery,
    CodeLocationComponentTypesQueryVariables
  >(CODE_LOCATION_COMPONENT_TYPES_QUERY, {
    variables: {locationName},
  });

  const editableTypes = useMemo<PickableType[]>(() => {
    const payload = typesQ.data?.componentTypesForLocationOrError;
    if (payload?.__typename !== 'ComponentTypes') {
      return [];
    }
    return payload.componentTypes
      .filter((c) => c.isAppManaged)
      .map((c) => ({
        name: c.name,
        namespace: c.namespace,
        description: c.description,
        formSchema: c.formSchema,
      }))
      .sort((a, b) => COMMON_COLLATOR.compare(a.name, b.name));
  }, [typesQ.data]);

  const [selected, setSelected] = useState<PickableType | null>(null);
  const [search, setSearch] = useState('');

  // In edit mode, sync `selected` to the loaded component type as soon as
  // `editableTypes` is populated, so the form skips the pick step.
  const editTargetComponentType = isEdit ? props.editTarget.componentType : undefined;
  useEffect(() => {
    if (!isEdit || selected || editTargetComponentType === undefined) {
      return;
    }
    const match = editableTypes.find((t) => t.name === editTargetComponentType);
    if (match) {
      setSelected(match);
    }
  }, [isEdit, editableTypes, selected, editTargetComponentType]);
  const [editorState, setEditorState] = useState<AppManagedComponentEditorState>(() => ({
    componentId: isEdit ? props.editTarget.componentId : '',
    attributes: isEdit ? props.editTarget.attributes : '',
    isValid: isEdit,
  }));
  const [error, setError] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) {
      return editableTypes;
    }
    return editableTypes.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.namespace.toLowerCase().includes(q) ||
        (t.description?.toLowerCase().includes(q) ?? false),
    );
  }, [editableTypes, search]);

  const [setAppManagedComponent, {loading: saving}] = useMutation<
    SetAppManagedComponentMutation,
    SetAppManagedComponentMutationVariables
  >(SET_APP_MANAGED_COMPONENT_MUTATION, {
    refetchQueries: [
      {query: CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY, variables: {locationName}},
    ],
    awaitRefetchQueries: true,
  });

  const handleSubmit = useCallback(async () => {
    if (!selected || !editorState.isValid) {
      return;
    }
    setError(null);
    const result = await setAppManagedComponent({
      variables: {
        locationName,
        componentId: editorState.componentId,
        componentType: selected.name,
        attributes: editorState.attributes,
      },
    });
    const data = result.data?.setAppManagedComponent;
    switch (data?.__typename) {
      case 'SetAppManagedComponentSuccess': {
        const verb = isEdit ? 'Saved' : 'Added';
        showToast({intent: 'success', message: `${verb} ${editorState.componentId}`});
        if (isEdit) {
          props.onSaved({
            kind: 'edit',
            componentId: editorState.componentId,
            componentType: selected.name,
            prevAttributes: props.editTarget.attributes,
          });
        } else {
          props.onCreated({
            kind: 'add',
            componentId: editorState.componentId,
            componentType: selected.name,
          });
        }
        onClose();
        return;
      }
      case 'UnauthorizedError':
        setError(
          data.message ??
            (isEdit
              ? 'You do not have permission to edit components.'
              : 'You do not have permission to add components.'),
        );
        return;
      case 'PythonError':
        // Storage was written but the in-process reload rejected the change.
        // Hand off to the parent, which surfaces the failure modal with a
        // revert option, and close this dialog so the modal can take over.
        onFailed(
          isEdit
            ? {
                kind: 'edit',
                componentId: editorState.componentId,
                componentType: selected.name,
                prevAttributes: props.editTarget.attributes,
              }
            : {
                kind: 'add',
                componentId: editorState.componentId,
                componentType: selected.name,
              },
          data.message,
        );
        onClose();
        return;
      default:
        setError('Unexpected response from server.');
    }
  }, [
    editorState,
    isEdit,
    locationName,
    onClose,
    onFailed,
    props,
    selected,
    setAppManagedComponent,
  ]);

  const phase: 'pick' | 'form' = selected ? 'form' : 'pick';
  let submitLabel: string;
  if (saving && isEdit) {
    submitLabel = 'Saving…';
  } else if (saving) {
    submitLabel = 'Adding…';
  } else if (isEdit) {
    submitLabel = 'Save';
  } else {
    submitLabel = 'Add component';
  }

  const renderPickerBody = () => {
    if (typesQ.loading && !typesQ.data) {
      return (
        <Box padding={32} flex={{direction: 'row', justifyContent: 'center'}}>
          <SpinnerWithText label="Loading component types…" />
        </Box>
      );
    }
    if (editableTypes.length === 0) {
      return (
        <NonIdealState
          icon="info"
          title="No UI-creatable component types"
          description="This code location does not currently expose any component types that can be created from the UI."
        />
      );
    }
    return (
      <Box flex={{direction: 'column', gap: 12}}>
        <TextInput
          icon="search"
          placeholder="Search components"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          fill
        />
        <div className={styles.typeList}>
          {filtered.length === 0 ? (
            <Box padding={32} flex={{direction: 'row', justifyContent: 'center'}}>
              <span className={styles.emptyMatches}>No matches</span>
            </Box>
          ) : null}
          {filtered.map((t) => (
            <Box
              key={`${t.namespace}.${t.name}`}
              padding={{vertical: 12, horizontal: 16}}
              flex={{
                direction: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 16,
              }}
              className={styles.typeRow}
            >
              <Box flex={{direction: 'column', gap: 4}} className={styles.typeRowContent}>
                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                  <span className={styles.typeRowName}>{t.name}</span>
                  <Tag>{sourceLabel(t.namespace)}</Tag>
                </Box>
                <Text
                  size={14}
                  family="mono"
                  className={styles.typeRowNamespace}
                >{`${t.namespace}.${t.name}`}</Text>
                {t.description ? (
                  <span className={styles.typeRowDescription}>{firstParagraph(t.description)}</span>
                ) : null}
              </Box>
              <Button intent="primary" onClick={() => setSelected(t)}>
                Configure
              </Button>
            </Box>
          ))}
        </div>
      </Box>
    );
  };

  const renderFormBody = () => {
    if (!selected) {
      return null;
    }
    return (
      <Box flex={{direction: 'column', gap: 16}}>
        <Box flex={{direction: 'column', gap: 2}}>
          <span className={styles.headerName}>{selected.name}</span>
          <Text
            size={14}
            family="mono"
            className={styles.headerNamespace}
          >{`${selected.namespace}.${selected.name}`}</Text>
        </Box>
        {isEdit ? (
          <AppManagedComponentEditorBody
            key={`edit-${props.editTarget.componentId}`}
            isActive={props.isOpen}
            mode="edit"
            locationName={locationName}
            componentType={selected.name}
            componentId={props.editTarget.componentId}
            initialAttributes={props.editTarget.attributes}
            formSchema={selected.formSchema}
            onChange={setEditorState}
          />
        ) : (
          <AppManagedComponentEditorBody
            key={`add-${selected.name}`}
            isActive={props.isOpen}
            mode="add"
            locationName={locationName}
            componentType={selected.name}
            formSchema={selected.formSchema}
            onChange={setEditorState}
          />
        )}
      </Box>
    );
  };

  const showBackButton = phase === 'form' && !isEdit;

  return (
    <>
      <DialogBody>{phase === 'pick' ? renderPickerBody() : renderFormBody()}</DialogBody>
      <DialogFooter topBorder>
        {showBackButton ? (
          <div className={styles.backButton}>
            <ButtonLink
              onClick={() => setSelected(null)}
              disabled={saving}
              color={Colors.linkDefault()}
            >
              ← Back to component selection
            </ButtonLink>
          </div>
        ) : null}
        {error ? (
          <span
            className={
              showBackButton ? styles.errorTextWithBackButton : styles.errorTextWithoutBackButton
            }
          >
            {error}
          </span>
        ) : null}
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        {phase === 'form' ? (
          <Button intent="primary" onClick={handleSubmit} disabled={saving || !editorState.isValid}>
            {submitLabel}
          </Button>
        ) : null}
      </DialogFooter>
    </>
  );
};
