import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
  SpinnerWithText,
  Table,
  Tag,
  Text,
  Tooltip,
  showToast,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import {useMutation, useQuery} from '../apollo-client';
import {AppManagedComponentMutationFailedDialog} from './AppManagedComponentMutationFailedDialog';
import {
  AppManagedComponentEditTarget,
  AppManagedComponentTypePickerDialog,
} from './AppManagedComponentTypePickerDialog';
import {
  CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY,
  DELETE_APP_MANAGED_COMPONENT_MUTATION,
  SET_APP_MANAGED_COMPONENT_MUTATION,
} from './CodeLocationAppManagedComponentsQuery';
import {CODE_LOCATION_COMPONENTS_QUERY} from './CodeLocationComponentsQuery';
import {ComponentStateRefreshButton} from './ComponentStateRefreshButton';
import {AppManagedComponentMutationContext} from './appManagedComponentMutationContext';
import styles from './css/CodeLocationComponentInstancesSubtab.module.css';
import {DefsStateManagementType} from '../graphql/types';
import {
  CodeLocationAppManagedComponentsQuery,
  CodeLocationAppManagedComponentsQueryVariables,
  DeleteAppManagedComponentMutation,
  DeleteAppManagedComponentMutationVariables,
  SetAppManagedComponentMutation,
  SetAppManagedComponentMutationVariables,
} from './types/CodeLocationAppManagedComponentsQuery.types';
import {
  CodeLocationComponentsQuery,
  CodeLocationComponentsQueryVariables,
} from './types/CodeLocationComponentsQuery.types';
import {
  buildReloadFnForLocation,
  useRepositoryLocationReload,
} from '../nav/useRepositoryLocationReload';
import {TimeFromNow} from '../ui/TimeFromNow';
import {repoAddressAsURLString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

interface Props {
  repoAddress: RepoAddress;
  isAddOpen: boolean;
  setIsAddOpen: (open: boolean) => void;
}

type RowSource = 'app_managed' | 'code';

interface ComponentRow {
  componentId: string;
  componentType: string;
  source: RowSource;
  // ``attributes`` is populated for app-managed rows and empty for code-backed
  // ones (server-side limitation; see fetch_app_managed_components.py).
  attributes: string;
  defsStateKey: string | null;
  defsStateVersion: string | null;
  defsStateCreateTimestamp: number | null;
  defsStateManagementType: DefsStateManagementType | null;
}

interface FailedMutation {
  ctx: AppManagedComponentMutationContext;
  errorMessage: string;
}

export const CodeLocationComponentInstancesSubtab = ({
  repoAddress,
  isAddOpen,
  setIsAddOpen,
}: Props) => {
  // App-managed (editable) components: served directly from defs state storage,
  // so this works even when the location fails to load.
  const appManagedComponentsQ = useQuery<
    CodeLocationAppManagedComponentsQuery,
    CodeLocationAppManagedComponentsQueryVariables
  >(CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY, {
    variables: {locationName: repoAddress.location},
  });
  const {refetch: refetchComponents} = appManagedComponentsQ;

  // Code-backed (view-only) components: pulled from the location's repository
  // snapshot. Only available once the location is loaded.
  const componentsQ = useQuery<CodeLocationComponentsQuery, CodeLocationComponentsQueryVariables>(
    CODE_LOCATION_COMPONENTS_QUERY,
    {
      variables: {locationName: repoAddress.location},
      fetchPolicy: 'cache-and-network',
    },
  );

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

  const [editTarget, setEditTarget] = useState<AppManagedComponentEditTarget | null>(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [viewConfigTarget, setViewConfigTarget] = useState<ComponentRow | null>(null);
  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState<ComponentRow | null>(null);

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
  const pendingMutationRef = useRef<AppManagedComponentMutationContext | null>(null);
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

  // Per-componentId state info pulled from the unified components query.
  const stateInfoById = useMemo(() => {
    const payload = componentsQ.data?.componentsForLocationOrError;
    const map = new Map<
      string,
      {
        defsStateKey: string | null;
        defsStateVersion: string | null;
        defsStateCreateTimestamp: number | null;
        defsStateManagementType: DefsStateManagementType | null;
      }
    >();
    if (payload?.__typename !== 'Components') {
      return map;
    }
    for (const c of payload.components) {
      map.set(c.componentId, {
        defsStateKey: c.defsStateKey ?? null,
        defsStateVersion: c.defsStateInfo?.version ?? null,
        defsStateCreateTimestamp: c.defsStateInfo?.createTimestamp ?? null,
        defsStateManagementType: c.defsStateManagementType ?? null,
      });
    }
    return map;
  }, [componentsQ.data]);

  const rows: ComponentRow[] = useMemo(() => {
    const appManagedPayload = appManagedComponentsQ.data?.appManagedComponentsForLocationOrError;
    const codePayload = componentsQ.data?.componentsForLocationOrError;
    const out: ComponentRow[] = [];

    if (appManagedPayload?.__typename === 'AppManagedComponents') {
      for (const c of appManagedPayload.components) {
        const s = stateInfoById.get(c.componentId);
        out.push({
          componentId: c.componentId,
          componentType: c.componentType,
          source: 'app_managed',
          attributes: c.attributes,
          defsStateKey: s?.defsStateKey ?? null,
          defsStateVersion: s?.defsStateVersion ?? null,
          defsStateCreateTimestamp: s?.defsStateCreateTimestamp ?? null,
          defsStateManagementType: s?.defsStateManagementType ?? null,
        });
      }
    }

    if (codePayload?.__typename === 'Components') {
      for (const c of codePayload.components) {
        if (c.isAppManaged) {
          continue;
        }
        out.push({
          componentId: c.componentId,
          componentType: c.componentType,
          source: 'code',
          attributes: c.attributes ?? '',
          defsStateKey: c.defsStateKey ?? null,
          defsStateVersion: c.defsStateInfo?.version ?? null,
          defsStateCreateTimestamp: c.defsStateInfo?.createTimestamp ?? null,
          defsStateManagementType: c.defsStateManagementType ?? null,
        });
      }
    }

    return out;
  }, [appManagedComponentsQ.data, componentsQ.data, stateInfoById]);

  const [deleteAppManagedComponent, {loading: deleting}] = useMutation<
    DeleteAppManagedComponentMutation,
    DeleteAppManagedComponentMutationVariables
  >(DELETE_APP_MANAGED_COMPONENT_MUTATION, {
    refetchQueries: [
      {
        query: CODE_LOCATION_APP_MANAGED_COMPONENTS_QUERY,
        variables: {locationName: repoAddress.location},
      },
    ],
    awaitRefetchQueries: true,
  });

  // Used to revert an edit (re-set previous attributes) or recreate a deleted
  // component during the revert flow. Add-revert uses the delete mutation.
  const [setAppManagedComponentForRevert] = useMutation<
    SetAppManagedComponentMutation,
    SetAppManagedComponentMutationVariables
  >(SET_APP_MANAGED_COMPONENT_MUTATION);
  const [deleteAppManagedComponentForRevert] = useMutation<
    DeleteAppManagedComponentMutation,
    DeleteAppManagedComponentMutationVariables
  >(DELETE_APP_MANAGED_COMPONENT_MUTATION);

  const handleAddCreated = useCallback(
    (ctx: AppManagedComponentMutationContext) => {
      refetchComponents();
      pendingMutationRef.current = ctx;
      tryReload();
    },
    [refetchComponents, tryReload],
  );

  const handleSaved = useCallback(
    (ctx: AppManagedComponentMutationContext) => {
      refetchComponents();
      pendingMutationRef.current = ctx;
      tryReload();
    },
    [refetchComponents, tryReload],
  );

  const handleMutationFailed = useCallback(
    (ctx: AppManagedComponentMutationContext, errorMessage: string) => {
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
      const result = await deleteAppManagedComponentForRevert({
        variables: {
          locationName: repoAddress.location,
          componentId: ctx.componentId,
        },
      });
      const data = result.data?.deleteAppManagedComponent;
      switch (data?.__typename) {
        case 'DeleteAppManagedComponentSuccess':
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
      const result = await setAppManagedComponentForRevert({
        variables: {
          locationName: repoAddress.location,
          componentId: ctx.componentId,
          componentType: ctx.componentType,
          attributes: ctx.prevAttributes ?? '',
        },
      });
      const data = result.data?.setAppManagedComponent;
      switch (data?.__typename) {
        case 'SetAppManagedComponentSuccess':
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

  const handleConfirmDelete = useCallback(async () => {
    if (!confirmDeleteTarget) {
      return;
    }
    const target = confirmDeleteTarget;
    const result = await deleteAppManagedComponent({
      variables: {
        locationName: repoAddress.location,
        componentId: target.componentId,
      },
    });
    const data = result.data?.deleteAppManagedComponent;
    switch (data?.__typename) {
      case 'DeleteAppManagedComponentSuccess':
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
  }, [
    confirmDeleteTarget,
    deleteAppManagedComponent,
    handleMutationFailed,
    repoAddress.location,
    tryReload,
  ]);

  const libraryPath = `/locations/${repoAddressAsURLString(repoAddress)}/components/library`;

  // ---------- Loading / error / empty ----------

  if (appManagedComponentsQ.loading && !appManagedComponentsQ.data) {
    return (
      <Box padding={64} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading components…" />
      </Box>
    );
  }

  const payload = appManagedComponentsQ.data?.appManagedComponentsForLocationOrError;
  if (appManagedComponentsQ.error || !payload || payload.__typename === 'PythonError') {
    return (
      <Box padding={32}>
        <NonIdealState
          icon="error"
          title="Could not load components"
          description={
            payload && payload.__typename !== 'AppManagedComponents'
              ? payload.message
              : (appManagedComponentsQ.error?.message ?? 'Unknown error')
          }
        />
      </Box>
    );
  }

  const failureModal = (
    <AppManagedComponentMutationFailedDialog
      isOpen={failedMutation !== null}
      ctx={failedMutation?.ctx ?? null}
      errorMessage={failedMutation?.errorMessage ?? ''}
      isReverting={isReverting}
      onRevert={handleRevert}
      onDismiss={handleDismissFailure}
    />
  );

  const dialogs = (
    <>
      <AppManagedComponentTypePickerDialog
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onCreated={handleAddCreated}
        onFailed={handleMutationFailed}
        locationName={repoAddress.location}
      />
      {editTarget ? (
        <AppManagedComponentTypePickerDialog
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
              Are you sure you want to delete{' '}
              <Text size={14} family="mono">
                {confirmDeleteTarget?.componentId ?? ''}
              </Text>
              ?
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
      {failureModal}
    </>
  );

  if (rows.length === 0) {
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
        <Table style={{width: '100%'}}>
          <thead>
            <tr>
              <th>Component</th>
              <th style={{width: 160}}>Source</th>
              <th style={{width: 280}}>State</th>
              <th style={{width: 48}} />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <ComponentRowView
                key={`${row.source}:${row.componentId}`}
                row={row}
                locationName={repoAddress.location}
                onEdit={() => {
                  setEditTarget(row);
                  setIsEditOpen(true);
                }}
                onViewConfig={() => setViewConfigTarget(row)}
                onDelete={() => setConfirmDeleteTarget(row)}
              />
            ))}
          </tbody>
        </Table>
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

interface ComponentRowViewProps {
  row: ComponentRow;
  locationName: string;
  onEdit: () => void;
  onViewConfig: () => void;
  onDelete: () => void;
}

const ComponentRowView = ({
  row,
  locationName,
  onEdit,
  onViewConfig,
  onDelete,
}: ComponentRowViewProps) => (
  <tr>
    <td>
      <Box flex={{direction: 'column', gap: 2}}>
        <span className={styles.rowId}>{row.componentId}</span>
        <span className={styles.rowType}>{row.componentType}</span>
      </Box>
    </td>
    <td>
      <SourceTag source={row.source} />
    </td>
    <td>
      <StateCell row={row} locationName={locationName} />
    </td>
    <td>
      {row.source === 'app_managed' ? (
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
      ) : null}
    </td>
  </tr>
);

const SourceTag = ({source}: {source: RowSource}) =>
  source === 'app_managed' ? (
    <Tag intent="primary" icon="edit">
      App-managed
    </Tag>
  ) : (
    <Tag icon="source">Code-backed</Tag>
  );

interface StateCellProps {
  row: ComponentRow;
  locationName: string;
}

const StateCell = ({row, locationName}: StateCellProps) => {
  if (!row.defsStateManagementType) {
    return <span style={{color: Colors.textLight()}}>—</span>;
  }
  if (row.defsStateManagementType === DefsStateManagementType.LOCAL_FILESYSTEM) {
    return (
      <Tooltip
        content="State is stored on the local filesystem or in the deployed image"
        placement="top"
      >
        <Tag>local filesystem</Tag>
      </Tooltip>
    );
  }
  if (row.defsStateManagementType === DefsStateManagementType.LEGACY_CODE_SERVER_SNAPSHOTS) {
    return (
      <Tooltip content="State is stored in-memory on the code server" placement="top">
        <Tag>code server</Tag>
      </Tooltip>
    );
  }
  // VERSIONED_STATE_STORAGE: single green bubble with TimeFromNow (built-in
  // hover tooltip shows the full timestamp).
  if (!row.defsStateCreateTimestamp) {
    return <span style={{color: Colors.textLight()}}>—</span>;
  }
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      <Tag intent="success" icon="check_circle">
        <TimeFromNow unixTimestamp={row.defsStateCreateTimestamp} />
      </Tag>
      {row.defsStateKey ? (
        <ComponentStateRefreshButton
          locationName={locationName}
          defsStateKey={row.defsStateKey}
          previousVersion={row.defsStateVersion}
        />
      ) : null}
    </Box>
  );
};

const ViewConfigDialog = ({
  target,
  onClose,
}: {
  target: ComponentRow | null;
  onClose: () => void;
}) => {
  const [content, setContent] = useState<ComponentRow | null>(target);
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
                <Text size={14} family="mono">
                  {content.componentType}
                </Text>
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
