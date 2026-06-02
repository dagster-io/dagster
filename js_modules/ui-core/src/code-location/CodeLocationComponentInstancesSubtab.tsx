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
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import {useMutation, useQuery} from '../apollo-client';
import {
  CODE_LOCATION_UI_COMPONENTS_QUERY,
  DELETE_UI_COMPONENT_MUTATION,
  SET_UI_COMPONENT_MUTATION,
} from './CodeLocationUIComponentsQuery';
import {UIComponentMutationFailedDialog} from './UIComponentMutationFailedDialog';
import {UIComponentEditTarget, UIComponentTypePickerDialog} from './UIComponentTypePickerDialog';
import styles from './css/CodeLocationComponentInstancesSubtab.module.css';
import {
  CodeLocationUiComponentsQuery,
  CodeLocationUiComponentsQueryVariables,
  DeleteUiComponentMutation,
  DeleteUiComponentMutationVariables,
  SetUiComponentMutation,
  SetUiComponentMutationVariables,
} from './types/CodeLocationUIComponentsQuery.types';
import {UIComponentMutationContext} from './uiComponentMutationContext';
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

interface FailedMutation {
  ctx: UIComponentMutationContext;
  errorMessage: string;
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
  const {
    reloading,
    tryReload,
    error: reloadError,
  } = useRepositoryLocationReload({
    scope: 'location',
    reloadFn,
  });

  const [editTarget, setEditTarget] = useState<UIComponentEditTarget | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [viewConfigTarget, setViewConfigTarget] = useState<UIBackedRow | null>(null);
  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState<UIBackedRow | null>(null);

  // Last mutation that returned a PythonError. The failure dialog renders
  // while this is set; dismissing or successfully reverting clears it.
  const [failedMutation, setFailedMutation] = useState<FailedMutation | null>(null);
  const [isReverting, setIsReverting] = useState(false);

  // ``useRepositoryLocationReload`` does its own reload + bounded poll (default
  // 3-minute deadline). If the just-completed add/edit/delete drove the
  // location into a failed state, the hook surfaces that error here — we
  // attribute it to whichever mutation we just kicked off and pop the revert
  // dialog. Tracked with a ref instead of state so handlers can publish a new
  // pending context without waiting for a render.
  const pendingMutationRef = useRef<UIComponentMutationContext | null>(null);
  const wasReloadingRef = useRef(false);

  useEffect(() => {
    // Catch the transition from "reload in flight" → "reload settled". At
    // that point ``reloadError`` reflects the final state of the poll loop;
    // attribute it to whatever the user just did (if anything). On a clean
    // reload we just clear the pending context — no dialog.
    if (wasReloadingRef.current && !reloading) {
      const ctx = pendingMutationRef.current;
      pendingMutationRef.current = null;
      if (ctx && reloadError) {
        const message =
          'message' in reloadError ? reloadError.message : 'Code location reload failed.';
        setFailedMutation({ctx, errorMessage: message});
      }
    }
    wasReloadingRef.current = reloading;
  }, [reloading, reloadError]);

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

  // Used to revert an edit (re-set previous attributes) or recreate a deleted
  // component during the revert flow. Add-revert uses the delete mutation.
  const [setUIComponentForRevert] = useMutation<
    SetUiComponentMutation,
    SetUiComponentMutationVariables
  >(SET_UI_COMPONENT_MUTATION);
  const [deleteUIComponentForRevert] = useMutation<
    DeleteUiComponentMutation,
    DeleteUiComponentMutationVariables
  >(DELETE_UI_COMPONENT_MUTATION);

  const handleAddCreated = useCallback(
    (ctx: UIComponentMutationContext) => {
      refetchComponents();
      pendingMutationRef.current = ctx;
      tryReload();
    },
    [refetchComponents, tryReload],
  );

  const handleSaved = useCallback(
    (ctx: UIComponentMutationContext) => {
      refetchComponents();
      pendingMutationRef.current = ctx;
      tryReload();
    },
    [refetchComponents, tryReload],
  );

  const handleMutationFailed = useCallback(
    (ctx: UIComponentMutationContext, errorMessage: string) => {
      setFailedMutation({ctx, errorMessage});
    },
    [],
  );

  const handleDismissFailure = useCallback(() => {
    setFailedMutation(null);
  }, []);

  const handleRevert = async () => {
    if (!failedMutation) {
      return;
    }
    const {ctx} = failedMutation;
    setIsReverting(true);
    let errorMessage: string | null = null;
    if (ctx.kind === 'add') {
      const result = await deleteUIComponentForRevert({
        variables: {
          locationName: repoAddress.location,
          componentId: ctx.componentId,
        },
      });
      const data = result.data?.deleteUIComponent;
      switch (data?.__typename) {
        case 'DeleteUIComponentSuccess':
          break;
        case 'UnauthorizedError':
          errorMessage = data.message ?? 'You do not have permission to revert this change.';
          break;
        case 'PythonError':
          errorMessage = data.message;
          break;
        default:
          errorMessage = 'Unexpected response from server.';
      }
    } else {
      // Revert an edit or a delete by re-setting the prior attributes.
      const result = await setUIComponentForRevert({
        variables: {
          locationName: repoAddress.location,
          componentId: ctx.componentId,
          componentType: ctx.componentType,
          attributes: ctx.prevAttributes ?? '',
        },
      });
      const data = result.data?.setUIComponent;
      switch (data?.__typename) {
        case 'SetUIComponentSuccess':
          break;
        case 'UnauthorizedError':
          errorMessage = data.message ?? 'You do not have permission to revert this change.';
          break;
        case 'PythonError':
          errorMessage = data.message;
          break;
        default:
          errorMessage = 'Unexpected response from server.';
      }
    }
    setIsReverting(false);
    if (errorMessage !== null) {
      showToast({intent: 'danger', message: errorMessage});
      return;
    }
    showToast({intent: 'success', message: `Reverted change to ${ctx.componentId}`});
    setFailedMutation(null);
    tryReload();
    refetchComponents();
  };

  const handleConfirmDelete = async () => {
    if (!confirmDeleteTarget) {
      return;
    }
    const target = confirmDeleteTarget;
    const result = await deleteUIComponent({
      variables: {
        locationName: repoAddress.location,
        componentId: target.componentId,
      },
    });
    const data = result.data?.deleteUIComponent;
    switch (data?.__typename) {
      case 'DeleteUIComponentSuccess':
        showToast({intent: 'success', message: `Deleted ${target.componentId}`});
        setConfirmDeleteTarget(null);
        pendingMutationRef.current = {
          kind: 'delete',
          componentId: target.componentId,
          componentType: target.componentType,
          prevAttributes: target.attributes,
        };
        tryReload();
        return;
      case 'UnauthorizedError':
        showToast({
          intent: 'danger',
          message: data.message ?? 'You do not have permission to delete components.',
        });
        return;
      case 'PythonError':
        // Storage was written but the in-process reload rejected the change.
        // Close the confirm dialog so the failure dialog sits cleanly on top.
        setConfirmDeleteTarget(null);
        handleMutationFailed(
          {
            kind: 'delete',
            componentId: target.componentId,
            componentType: target.componentType,
            prevAttributes: target.attributes,
          },
          data.message,
        );
        return;
    }
  };

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
        onCreated={handleAddCreated}
        onFailed={handleMutationFailed}
        locationName={repoAddress.location}
      />
      {editTarget ? (
        <UIComponentTypePickerDialog
          mode="edit"
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          onSaved={handleSaved}
          onFailed={handleMutationFailed}
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
      <UIComponentMutationFailedDialog
        isOpen={failedMutation !== null}
        ctx={failedMutation?.ctx ?? null}
        errorMessage={failedMutation?.errorMessage ?? ''}
        isReverting={isReverting}
        onRevert={handleRevert}
        onDismiss={handleDismissFailure}
      />
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
