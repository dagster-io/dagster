import {
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Mono,
  NonIdealState,
  Popover,
  SpinnerWithText,
  showToast,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useCallback, useEffect, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {useMutation, useQuery} from '../apollo-client';
import {
  CODE_LOCATION_UI_COMPONENTS_QUERY,
  DELETE_UI_COMPONENT_MUTATION,
} from './CodeLocationUIComponentsQuery';
import {UIComponentEditTarget, UIComponentTypePickerDialog} from './UIComponentTypePickerDialog';
import styles from './css/CodeLocationComponentInstancesSubtab.module.css';
import {
  CodeLocationUiComponentsQuery,
  CodeLocationUiComponentsQueryVariables,
  DeleteUiComponentMutation,
  DeleteUiComponentMutationVariables,
} from './types/CodeLocationUIComponentsQuery.types';
import {
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  isAddOpen: boolean;
  setIsAddOpen: (open: boolean) => void;
}

interface UIBackedRow {
  componentId: string;
  componentType: string;
  attributes: string;
}

export const CodeLocationComponentInstancesSubtab = ({
  repoAddress,
  isAddOpen,
  setIsAddOpen,
}: Props) => {
  const componentsQ = useQuery<
    CodeLocationUiComponentsQuery,
    CodeLocationUiComponentsQueryVariables
  >(CODE_LOCATION_UI_COMPONENTS_QUERY, {
    variables: {locationName: repoAddress.location},
  });
  const {refetch: refetchComponents} = componentsQ;

  const reloadFn = useMemo(
    () => buildReloadFnForLocation(repoAddress.location),
    [repoAddress.location],
  );
  const {reloading, tryReload} = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  const [editTarget, setEditTarget] = useState<UIComponentEditTarget | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [viewConfigTarget, setViewConfigTarget] = useState<UIBackedRow | null>(null);
  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState<UIBackedRow | null>(null);
  const uiBackedRows: UIBackedRow[] = useMemo(() => {
    const payload = componentsQ.data?.uiComponentsForLocationOrError;
    if (payload?.__typename !== 'UIComponents') {
      return [];
    }
    return payload.components.map(
      (c): UIBackedRow => ({
        componentId: c.componentId,
        componentType: c.componentType,
        attributes: c.attributes,
      }),
    );
  }, [componentsQ.data]);

  const [deleteUIComponent, {loading: deleting}] = useMutation<
    DeleteUiComponentMutation,
    DeleteUiComponentMutationVariables
  >(DELETE_UI_COMPONENT_MUTATION, {
    refetchQueries: [
      {
        query: CODE_LOCATION_UI_COMPONENTS_QUERY,
        variables: {locationName: repoAddress.location},
      },
    ],
    awaitRefetchQueries: true,
  });

  const handleAddSucceeded = useCallback(() => {
    refetchComponents();
    tryReload();
  }, [refetchComponents, tryReload]);

  const handleSaved = useCallback(() => {
    refetchComponents();
    tryReload();
  }, [refetchComponents, tryReload]);

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDeleteTarget) {
      return;
    }
    const result = await deleteUIComponent({
      variables: {
        locationName: repoAddress.location,
        componentId: confirmDeleteTarget.componentId,
      },
    });
    const data = result.data?.deleteUIComponent;
    switch (data?.__typename) {
      case 'DeleteUIComponentSuccess':
        showToast({intent: 'success', message: `Deleted ${confirmDeleteTarget.componentId}`});
        setConfirmDeleteTarget(null);
        tryReload();
        return;
      case 'UnauthorizedError':
        showToast({
          intent: 'danger',
          message: data.message ?? 'You do not have permission to delete components.',
        });
        return;
      case 'PythonError':
        showToast({intent: 'danger', message: data.message});
    }
  }, [confirmDeleteTarget, deleteUIComponent, repoAddress.location, tryReload]);

  const libraryPath = `/locations/${repoAddressAsURLString(repoAddress)}/components/library`;

  // ---------- Loading / error / empty ----------

  if (componentsQ.loading && !componentsQ.data) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading components…" />
      </Box>
    );
  }

  const payload = componentsQ.data?.uiComponentsForLocationOrError;
  if (componentsQ.error || !payload || payload.__typename === 'PythonError') {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="Could not load components"
          description={
            payload && payload.__typename !== 'UIComponents'
              ? payload.message
              : (componentsQ.error?.message ?? 'Unknown error')
          }
        />
      </Box>
    );
  }

  const dialogs = (
    <>
      <UIComponentTypePickerDialog
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onCreated={handleAddSucceeded}
        locationName={repoAddress.location}
      />
      {editTarget ? (
        <UIComponentTypePickerDialog
          mode="edit"
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          onSaved={handleSaved}
          editTarget={editTarget}
          locationName={repoAddress.location}
        />
      ) : null}
      <ViewConfigDialog target={viewConfigTarget} onClose={() => setViewConfigTarget(null)} />
      <Dialog
        isOpen={confirmDeleteTarget !== null}
        title="Delete component"
        onClose={() => !deleting && setConfirmDeleteTarget(null)}
        icon="info"
      >
        <DialogBody>
          <Box flex={{direction: 'column', gap: 8}}>
            <span>
              Are you sure you want to delete <Mono>{confirmDeleteTarget?.componentId ?? ''}</Mono>?
            </span>
            <span>This will remove the component from the code location and cannot be undone.</span>
          </Box>
        </DialogBody>
        <DialogFooter topBorder>
          <Button onClick={() => setConfirmDeleteTarget(null)} disabled={deleting}>
            Cancel
          </Button>
          <Button intent="danger" onClick={handleConfirmDelete} disabled={deleting}>
            {deleting ? 'Deleting…' : 'Delete'}
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );

  if (uiBackedRows.length === 0) {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="code_location"
          title="No component instances found"
          description={
            <Box flex={{direction: 'column', gap: 8, alignItems: 'center'}}>
              <span>
                Each Dagster project ships with a menu of components for standard Dagster workflows.
                You can also install dozens of other Dagster-managed components or develop your own.
                Dagster will track any instances of your components in this code location here.
              </span>
            </Box>
          }
          action={
            <Box flex={{direction: 'row', gap: 8}}>
              <Button
                intent="primary"
                icon={<Icon name="add_circle" />}
                onClick={() => setIsAddOpen(true)}
              >
                Add
              </Button>
              <Link to={libraryPath}>
                <Button icon={<Icon name="folder" />}>View component docs</Button>
              </Link>
            </Box>
          }
        />
        {dialogs}
      </Box>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.scrollArea}>
        {uiBackedRows.map((row) => (
          <UIBackedRowView
            key={row.componentId}
            row={row}
            onEdit={() => {
              setEditTarget(row);
              setIsEditOpen(true);
            }}
            onViewConfig={() => setViewConfigTarget(row)}
            onDelete={() => setConfirmDeleteTarget(row)}
          />
        ))}
      </div>
      {reloading ? (
        <div className={styles.reloadOverlay}>
          <div className={styles.reloadOverlayInner}>
            <SpinnerWithText label="Reloading code location…" />
          </div>
        </div>
      ) : null}
      {dialogs}
    </div>
  );
};

interface UIBackedRowViewProps {
  row: UIBackedRow;
  onEdit: () => void;
  onViewConfig: () => void;
  onDelete: () => void;
}

const UIBackedRowView = ({row, onEdit, onViewConfig, onDelete}: UIBackedRowViewProps) => (
  <div className={styles.row}>
    <span className={styles.rowId}>{row.componentId}</span>
    <span className={styles.rowType}>{row.componentType}</span>
    <span />
    <div className={styles.rowRight}>
      <Popover
        position="bottom-right"
        content={
          <Menu>
            <MenuItem icon="edit" text="Edit" onClick={onEdit} />
            <MenuItem icon="info" text="View config" onClick={onViewConfig} />
            <MenuItem icon="delete" intent="danger" text="Delete" onClick={onDelete} />
          </Menu>
        }
      >
        <Button icon={<Icon name="more_horiz" />} />
      </Popover>
    </div>
  </div>
);

const ViewConfigDialog = ({target, onClose}: {target: UIBackedRow | null; onClose: () => void}) => {
  const [content, setContent] = useState<UIBackedRow | null>(target);
  useEffect(() => {
    if (target) {
      setContent(target);
    }
  }, [target]);
  return (
    <Dialog
      isOpen={target !== null}
      onClose={onClose}
      title={content?.componentId ?? ''}
      icon="info"
      style={{maxWidth: '90%', minWidth: '60%', width: 800}}
    >
      {content ? (
        <>
          <DialogBody>
            <Box flex={{direction: 'column', gap: 12}}>
              <Box flex={{direction: 'column', gap: 4}}>
                <span className={styles.fieldLabel}>Component type</span>
                <Mono>{content.componentType}</Mono>
              </Box>
              <Box flex={{direction: 'column', gap: 4}}>
                <span className={styles.fieldLabel}>Attributes</span>
                <Box border="all" className={styles.editorFrame}>
                  <StyledRawCodeMirror
                    value={content.attributes}
                    options={{mode: 'yaml', lineNumbers: true, readOnly: true}}
                    handlers={{onChange: () => {}}}
                  />
                </Box>
              </Box>
            </Box>
          </DialogBody>
          <DialogFooter topBorder>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </>
      ) : null}
    </Dialog>
  );
};
