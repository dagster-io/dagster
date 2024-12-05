import {
  Box,
  Button,
  ButtonLink,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Heading,
  Icon,
  Menu,
  MenuItem,
  MetadataTableWIP,
  Mono,
  NonIdealState,
  Page,
  PageHeader,
  Popover,
  Spinner,
  Subheading,
  Table,
  Tag,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import {StyledRawCodeMirror} from '@dagster-io/ui-components/editor';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {ConcurrencyTable} from './VirtualizedInstanceConcurrencyTable';
import {gql, useMutation, useQuery} from '../apollo-client';
import {
  ConcurrencyKeyDetailsQuery,
  ConcurrencyKeyDetailsQueryVariables,
  ConcurrencyLimitFragment,
  ConcurrencyStepFragment,
  DeleteConcurrencyLimitMutation,
  DeleteConcurrencyLimitMutationVariables,
  FreeConcurrencySlotsMutation,
  FreeConcurrencySlotsMutationVariables,
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  RunQueueConfigFragment,
  RunsForConcurrencyKeyQuery,
  RunsForConcurrencyKeyQueryVariables,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/InstanceConcurrency.types';
import {showSharedToaster} from '../app/DomUtils';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {COMMON_COLLATOR} from '../app/Util';
import {useTrackPageView} from '../app/analytics';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RunStatusDot} from '../runs/RunStatusDots';
import {failedStatuses} from '../runs/RunStatuses';
import {titleForRun} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';

const DEFAULT_MIN_VALUE = 1;
const DEFAULT_MAX_VALUE = 1000;

export const InstanceConcurrencyPageContent = React.memo(() => {
  useTrackPageView();
  useDocumentTitle('Concurrency');
  const [selectedKey, setSelectedKey] = useQueryPersistedState<string | undefined>({
    queryKey: 'key',
  });
  const queryResult = useQuery<
    InstanceConcurrencyLimitsQuery,
    InstanceConcurrencyLimitsQueryVariables
  >(INSTANCE_CONCURRENCY_LIMITS_QUERY, {
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;

  return (
    <div style={{overflowY: 'auto'}}>
      {data ? (
        <>
          <Box margin={{bottom: 64}}>
            <RunConcurrencyContent
              refreshState={refreshState}
              hasRunQueue={!!data?.instance.runQueuingSupported}
              runQueueConfig={data?.instance.runQueueConfig}
            />
          </Box>
          <ConcurrencyLimits
            instanceConfig={data.instance.info}
            concurrencyKeys={data.instance.concurrencyLimits.map((limit) => limit.concurrencyKey)}
            hasSupport={data.instance.supportsConcurrencyLimits}
            refetch={queryResult.refetch}
            minValue={data.instance.minConcurrencyLimitValue}
            maxValue={data.instance.maxConcurrencyLimitValue}
            selectedKey={selectedKey}
            onSelectKey={setSelectedKey}
          />
        </>
      ) : (
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      )}
    </div>
  );
});

export const InstanceConcurrencyPage = () => {
  const {pageTitle} = React.useContext(InstancePageContext);
  return (
    <Page style={{padding: 0}}>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="concurrency" />}
      />
      <InstanceConcurrencyPageContent />
    </Page>
  );
};

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default InstanceConcurrencyPage;

type DialogAction =
  | {
      actionType: 'add';
    }
  | {
      actionType: 'edit';
      concurrencyKey: string;
    }
  | {
      actionType: 'delete';
      concurrencyKey: string;
    }
  | undefined;

export const RunConcurrencyContent = ({
  hasRunQueue,
  runQueueConfig,
  onEdit,
  refreshState,
}: {
  hasRunQueue: boolean;
  runQueueConfig: RunQueueConfigFragment | null | undefined;
  refreshState?: QueryRefreshState;
  onEdit?: () => void;
}) => {
  if (!hasRunQueue) {
    return (
      <>
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border="bottom"
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        >
          <Subheading>Run concurrency</Subheading>
          {refreshState ? <QueryRefreshCountdown refreshState={refreshState} /> : null}
        </Box>
        <Box padding={{vertical: 16, horizontal: 24}}>
          Run concurrency is not supported with this run coordinator. To enable run concurrency
          limits, configure your instance to use the <Mono>QueuedRunCoordinator</Mono> in your{' '}
          <Mono>dagster.yaml</Mono>. See the{' '}
          <a
            target="_blank"
            rel="noreferrer"
            href="https://docs.dagster.io/deployment/dagster-instance#queuedruncoordinator"
          >
            QueuedRunCoordinator documentation
          </a>{' '}
          for more information.
        </Box>
      </>
    );
  }

  const infoContent = (
    <Box padding={{vertical: 16, horizontal: 24}}>
      Run concurrency can be set in your run queue settings. See the{' '}
      <a
        target="_blank"
        rel="noreferrer"
        href="https://docs.dagster.io/guides/limiting-concurrency-in-data-pipelines#configuring-run-level-concurrency"
      >
        run concurrency documentation
      </a>{' '}
      for more information.
    </Box>
  );

  const settings_content = runQueueConfig ? (
    <MetadataTableWIP>
      <tbody>
        <tr>
          <td>Max concurrent runs:</td>
          <td>{runQueueConfig.maxConcurrentRuns}</td>
        </tr>
        <tr>
          <td>Tag concurrency limits:</td>
          <td>
            {runQueueConfig.tagConcurrencyLimitsYaml ? (
              <StyledRawCodeMirror
                value={runQueueConfig.tagConcurrencyLimitsYaml}
                options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
              />
            ) : (
              '-'
            )}
          </td>
        </tr>
      </tbody>
    </MetadataTableWIP>
  ) : null;

  return (
    <>
      <RunConcurrencyLimitHeader onEdit={onEdit} refreshState={refreshState} />
      {infoContent}
      {settings_content}
    </>
  );
};

const RunConcurrencyLimitHeader = ({
  onEdit,
  refreshState,
}: {
  onEdit?: () => void;
  refreshState?: QueryRefreshState;
}) => (
  <Box
    flex={{justifyContent: 'space-between', alignItems: 'center'}}
    padding={{vertical: 16, horizontal: 24}}
    border="bottom"
  >
    <Subheading>Run concurrency</Subheading>
    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
      {refreshState ? <QueryRefreshCountdown refreshState={refreshState} /> : null}
      {onEdit ? (
        <Button icon={<Icon name="edit" />} onClick={() => onEdit()}>
          Edit configuration
        </Button>
      ) : null}
    </Box>
  </Box>
);

export const ConcurrencyLimits = ({
  instanceConfig,
  hasSupport,
  concurrencyKeys,
  refetch,
  minValue,
  maxValue,
  selectedKey,
  onSelectKey,
}: {
  concurrencyKeys: string[];
  refetch: () => void;
  instanceConfig?: string | null;
  hasSupport?: boolean;
  maxValue?: number;
  minValue?: number;
  selectedKey?: string | null;
  onSelectKey: (key: string | undefined) => void;
}) => {
  const [action, setAction] = React.useState<DialogAction>();
  const onConcurrencyStepsDialogClose = React.useCallback(() => {
    onSelectKey(undefined);
  }, [onSelectKey]);

  const [search, setSearch] = React.useState('');

  const sortedKeys = React.useMemo(() => {
    return [...concurrencyKeys]
      .filter((key) => key.includes(search))
      .sort((a, b) => COMMON_COLLATOR.compare(a, b));
  }, [concurrencyKeys, search]);

  const onAdd = () => {
    setAction({actionType: 'add'});
  };
  const onEdit = (concurrencyKey: string) => {
    setAction({actionType: 'edit', concurrencyKey});
  };
  const onDelete = (concurrencyKey: string) => {
    setAction({actionType: 'delete', concurrencyKey});
  };

  if (!hasSupport && instanceConfig && instanceConfig.includes('SqliteEventLogStorage')) {
    return (
      <>
        <ConcurrencyLimitHeader />
        <Box margin={24}>
          <NonIdealState
            icon="error"
            title="No concurrency support"
            description={
              'This instance does not support global concurrency limits. You will need to ' +
              'configure a different storage implementation (e.g. Postgres/MySQL) to use this ' +
              'feature.'
            }
          />
        </Box>
      </>
    );
  } else if (hasSupport === false) {
    return (
      <>
        <ConcurrencyLimitHeader />
        <Box margin={24}>
          <NonIdealState
            icon="error"
            title="No concurrency support"
            description={
              'This instance does not currently support global concurrency limits. You may need to ' +
              'run `dagster instance migrate` to add the necessary tables to your dagster storage ' +
              'to support this feature.'
            }
          />
        </Box>
      </>
    );
  }

  return (
    <Box flex={{direction: 'column'}} style={{overflow: 'auto', height: '100%'}}>
      <ConcurrencyLimitHeader onAdd={onAdd} search={search} setSearch={setSearch} />
      {concurrencyKeys.length === 0 ? (
        <Box margin={24}>
          <NonIdealState
            icon="error"
            title="No concurrency limits"
            description={
              <>
                No concurrency limits have been configured for this instance.&nbsp;
                <ButtonLink onClick={() => onAdd()}>Add a concurrency limit</ButtonLink>.
              </>
            }
          />
        </Box>
      ) : (
        <ConcurrencyTable
          concurrencyKeys={sortedKeys}
          onDelete={onDelete}
          onEdit={onEdit}
          onSelect={onSelectKey}
        />
      )}
      <AddConcurrencyLimitDialog
        open={action?.actionType === 'add'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
        minValue={minValue ?? DEFAULT_MIN_VALUE}
        maxValue={maxValue ?? DEFAULT_MAX_VALUE}
      />
      <DeleteConcurrencyLimitDialog
        concurrencyKey={action && action.actionType === 'delete' ? action.concurrencyKey : ''}
        open={action?.actionType === 'delete'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
      />
      <EditConcurrencyLimitDialog
        open={action?.actionType === 'edit'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
        concurrencyKey={action?.actionType === 'edit' ? action.concurrencyKey : ''}
        minValue={minValue ?? DEFAULT_MIN_VALUE}
        maxValue={maxValue ?? DEFAULT_MAX_VALUE}
      />
      <ConcurrencyStepsDialog
        title={
          <span>
            Concurrency steps for <strong>{selectedKey}</strong>
          </span>
        }
        onClose={onConcurrencyStepsDialogClose}
        concurrencyKey={selectedKey}
        onUpdate={refetch}
      />
    </Box>
  );
};

const ConcurrencyLimitHeader = ({
  onAdd,
  setSearch,
  search,
}: {
  onAdd?: () => void;
} & (
  | {
      setSearch: (searchString: string) => void;
      search: string;
    }
  | {setSearch?: never; search?: never}
)) => {
  return (
    <Box flex={{direction: 'column'}}>
      <Box
        flex={{justifyContent: 'space-between', alignItems: 'center'}}
        padding={{vertical: 16, horizontal: 24}}
        border="top-and-bottom"
      >
        <Box flex={{alignItems: 'center', direction: 'row', gap: 8}}>
          <Subheading>Global op/asset concurrency</Subheading>
          <Tag>Experimental</Tag>
        </Box>
        {onAdd ? (
          <Button icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
            Add concurrency limit
          </Button>
        ) : null}
      </Box>
      {setSearch ? (
        <Box flex={{direction: 'row'}} padding={{vertical: 16, horizontal: 24}} border="bottom">
          <TextInput
            value={search || ''}
            style={{width: '30vw', minWidth: 150, maxWidth: 400}}
            placeholder="Filter concurrency keys"
            onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
          />
        </Box>
      ) : null}
    </Box>
  );
};

const isValidLimit = (
  concurrencyLimit?: string,
  minLimitValue: number = DEFAULT_MIN_VALUE,
  maxLimitValue: number = DEFAULT_MAX_VALUE,
) => {
  if (!concurrencyLimit) {
    return false;
  }
  const value = parseInt(concurrencyLimit);
  if (isNaN(value)) {
    return false;
  }
  if (String(value) !== concurrencyLimit.trim()) {
    return false;
  }
  return value >= minLimitValue && value <= maxLimitValue;
};

const AddConcurrencyLimitDialog = ({
  open,
  onClose,
  onComplete,
  maxValue,
  minValue,
}: {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
  maxValue: number;
  minValue: number;
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState('');
  const [keyInput, setKeyInput] = React.useState('');

  React.useEffect(() => {
    setLimitInput('');
    setKeyInput('');
  }, [open]);

  const [setConcurrencyLimit] = useMutation<
    SetConcurrencyLimitMutation,
    SetConcurrencyLimitMutationVariables
  >(SET_CONCURRENCY_LIMIT_MUTATION);

  const save = async () => {
    setIsSubmitting(true);
    await setConcurrencyLimit({
      variables: {concurrencyKey: keyInput, limit: parseInt(limitInput.trim())},
    });
    setIsSubmitting(false);
    onComplete();
    onClose();
  };

  return (
    <Dialog isOpen={open} title="Add concurrency limit" onClose={onClose}>
      <DialogBody>
        <Box margin={{bottom: 4}}>Concurrency key:</Box>
        <Box margin={{bottom: 16}}>
          <TextInput
            value={keyInput || ''}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder="Concurrency key"
          />
        </Box>
        <Box margin={{bottom: 4}}>
          Concurrency limit ({minValue}-{maxValue}):
        </Box>
        <Box>
          <TextInput
            value={limitInput || ''}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder={`${minValue} - ${maxValue}`}
          />
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Cancel
        </Button>
        <Button
          intent="primary"
          onClick={save}
          disabled={
            !isValidLimit(limitInput.trim(), minValue, maxValue) || !keyInput || isSubmitting
          }
        >
          {isSubmitting ? 'Adding...' : 'Add limit'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const EditConcurrencyLimitDialog = ({
  concurrencyKey,
  open,
  onClose,
  onComplete,
  minValue,
  maxValue,
}: {
  concurrencyKey: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
  minValue: number;
  maxValue: number;
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState('');

  React.useEffect(() => {
    setLimitInput('');
  }, [open]);

  const [setConcurrencyLimit] = useMutation<
    SetConcurrencyLimitMutation,
    SetConcurrencyLimitMutationVariables
  >(SET_CONCURRENCY_LIMIT_MUTATION);

  const save = async () => {
    setIsSubmitting(true);
    await setConcurrencyLimit({
      variables: {concurrencyKey, limit: parseInt(limitInput!.trim())},
    });
    setIsSubmitting(false);
    onComplete();
    onClose();
  };

  const title = (
    <>
      Edit <Mono>{concurrencyKey}</Mono>
    </>
  );

  return (
    <Dialog isOpen={open} title={title} onClose={onClose}>
      <DialogBody>
        <Box margin={{bottom: 4}}>Concurrency key:</Box>
        <Box margin={{bottom: 16}}>
          <strong>{concurrencyKey}</strong>
        </Box>
        <Box margin={{bottom: 4}}>
          Concurrency limit ({minValue}-{maxValue}):
        </Box>
        <Box>
          <TextInput
            value={limitInput || ''}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder={`${minValue} - ${maxValue}`}
          />
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
        {isSubmitting ? (
          <Button intent="primary" disabled>
            Updating...
          </Button>
        ) : (
          <Button
            intent="primary"
            onClick={save}
            disabled={!isValidLimit(limitInput.trim(), minValue, maxValue)}
          >
            Update limit
          </Button>
        )}
      </DialogFooter>
    </Dialog>
  );
};

const DeleteConcurrencyLimitDialog = ({
  concurrencyKey,
  open,
  onClose,
  onComplete,
}: {
  concurrencyKey: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const [deleteConcurrencyLimit] = useMutation<
    DeleteConcurrencyLimitMutation,
    DeleteConcurrencyLimitMutationVariables
  >(DELETE_CONCURRENCY_LIMIT_MUTATION);

  const save = async () => {
    setIsSubmitting(true);
    await deleteConcurrencyLimit({variables: {concurrencyKey}});
    setIsSubmitting(false);
    onComplete();
    onClose();
  };

  const title = (
    <>
      Delete <Mono>{concurrencyKey}</Mono>
    </>
  );
  return (
    <Dialog isOpen={open} title={title} onClose={onClose}>
      <DialogBody>
        Delete concurrency limit&nbsp;<strong>{concurrencyKey}</strong>?
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
        {isSubmitting ? (
          <Button intent="danger" disabled>
            Deleting...
          </Button>
        ) : (
          <Button intent="danger" onClick={save}>
            Delete limit
          </Button>
        )}
      </DialogFooter>
    </Dialog>
  );
};

const ConcurrencyActionMenu = ({
  pendingStep,
  onUpdate,
}: {
  pendingStep: ConcurrencyStepFragment;
  onUpdate: () => void;
}) => {
  const [freeSlots] = useMutation<
    FreeConcurrencySlotsMutation,
    FreeConcurrencySlotsMutationVariables
  >(FREE_CONCURRENCY_SLOTS_MUTATION);

  return (
    <Popover
      content={
        <Menu>
          <MenuItem
            key="free-concurrency-slots-step"
            icon="status"
            text="Free concurrency slot for step"
            onClick={async () => {
              const resp = await freeSlots({
                variables: {runId: pendingStep.runId, stepKey: pendingStep.stepKey},
              });
              if (resp.data?.freeConcurrencySlots) {
                onUpdate();
                await showSharedToaster({
                  intent: 'success',
                  icon: 'copy_to_clipboard_done',
                  message: 'Freed concurrency slot',
                });
              }
            }}
          />
          <MenuItem
            key="free-concurrency-slots-run"
            icon="status"
            text="Free all concurrency slots for run"
            onClick={async () => {
              await showSharedToaster({message: 'Freeing concurrency slots...'});
              const resp = await freeSlots({variables: {runId: pendingStep.runId}});
              if (resp.data?.freeConcurrencySlots) {
                onUpdate();
                await showSharedToaster({
                  intent: 'success',
                  icon: 'copy_to_clipboard_done',
                  message: 'Freed concurrency slots',
                });
              }
            }}
          />
        </Menu>
      }
      position="bottom-right"
    >
      <Button rightIcon={<Icon name="expand_more" />}>Actions</Button>
    </Popover>
  );
};

const ConcurrencyStepsDialog = ({
  concurrencyKey,
  onClose,
  title,
  onUpdate,
}: {
  concurrencyKey?: string | null;
  title: string | React.ReactNode;
  onClose: () => void;
  onUpdate: () => void;
}) => {
  const queryResult = useQuery<ConcurrencyKeyDetailsQuery, ConcurrencyKeyDetailsQueryVariables>(
    CONCURRENCY_KEY_DETAILS_QUERY,
    {
      variables: {
        concurrencyKey: concurrencyKey || '',
      },
      skip: !concurrencyKey,
    },
  );
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;
  const refetch = React.useCallback(() => {
    queryResult.refetch();
    onUpdate();
  }, [queryResult, onUpdate]);

  return (
    <Dialog
      isOpen={!!concurrencyKey}
      title={title}
      onClose={onClose}
      style={{
        minWidth: '400px',
        maxWidth: '1000px',
        width: '90vw',
        maxHeight: '90vh',
      }}
    >
      <Box padding={{vertical: 16}} flex={{grow: 1}} style={{overflowY: 'auto'}}>
        {!data ? (
          <Box padding={{vertical: 64}}>
            <Spinner purpose="section" />
          </Box>
        ) : (
          <PendingStepsTable keyInfo={data.instance.concurrencyLimit} refresh={refetch} />
        )}
      </Box>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const PendingStepsTable = ({
  keyInfo,
  refresh,
}: {
  keyInfo: ConcurrencyLimitFragment;
  refresh: () => void;
}) => {
  const runIds = [...new Set(keyInfo.pendingSteps.map((step) => step.runId))];
  const queryResult = useQuery<RunsForConcurrencyKeyQuery, RunsForConcurrencyKeyQueryVariables>(
    RUNS_FOR_CONCURRENCY_KEY_QUERY,
    {
      variables: {
        filter: {runIds},
      },
      skip: !keyInfo.pendingSteps.length,
    },
  );
  const statusByRunId: {[id: string]: RunStatus} = {};
  const runs =
    queryResult.data?.pipelineRunsOrError.__typename === 'Runs'
      ? queryResult.data.pipelineRunsOrError.results
      : [];
  runs.forEach((run) => {
    statusByRunId[run.id] = run.status;
  });

  const steps = [...keyInfo.pendingSteps];
  steps.sort((a, b) => {
    if (a.priority && b.priority && a.priority !== b.priority) {
      return a.priority - b.priority;
    }
    return a.enqueuedTimestamp - b.enqueuedTimestamp;
  });
  const assignedSteps = steps.filter((step) => !!step.assignedTimestamp);
  const pendingSteps = steps.filter((step) => !step.assignedTimestamp);

  const tableHeader = (
    <thead>
      <tr>
        <th>Run ID</th>
        <th>Step key</th>
        <th>Assigned</th>
        <th>Queued</th>
        <th>
          <Box flex={{alignItems: 'center', direction: 'row', gap: 4}}>
            Priority
            <Tooltip
              placement="top"
              content="Priority can be set on each op/asset using the 'dagster/priority' tag. Higher priority steps will be assigned slots first."
            >
              <Icon name="info" color={Colors.accentGray()} />
            </Tooltip>
          </Box>
        </th>
        <th></th>
      </tr>
    </thead>
  );

  if (!steps.length) {
    return (
      <Table>
        {tableHeader}
        <tbody>
          <tr>
            <td colSpan={6}>
              <Box
                flex={{alignItems: 'center', justifyContent: 'center'}}
                style={{color: Colors.textLight()}}
                padding={16}
              >
                There are no active or pending steps for this concurrency key.
              </Box>
            </td>
          </tr>
        </tbody>
      </Table>
    );
  }

  return (
    <Table>
      {tableHeader}
      <tbody style={{backgroundColor: Colors.backgroundYellow()}}>
        {assignedSteps.map((step) => (
          <PendingStepRow
            key={step.runId + step.stepKey}
            step={step}
            statusByRunId={statusByRunId}
            onUpdate={refresh}
          />
        ))}
      </tbody>
      <tbody>
        {pendingSteps.map((step) => (
          <PendingStepRow
            key={step.runId + step.stepKey}
            step={step}
            statusByRunId={statusByRunId}
            onUpdate={refresh}
          />
        ))}
      </tbody>
    </Table>
  );
};

const PendingStepRow = ({
  step,
  statusByRunId,
  onUpdate,
}: {
  step: ConcurrencyStepFragment;
  statusByRunId: {[id: string]: RunStatus};
  onUpdate: () => void;
}) => {
  const runStatus = statusByRunId[step.runId];
  return (
    <tr>
      <td>
        {runStatus ? (
          <Link to={`/runs/${step.runId}`}>
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <RunStatusDot status={runStatus} size={10} />
              <Mono>{titleForRun({id: step.runId})}</Mono>
              {failedStatuses.has(runStatus) ? (
                <Tooltip
                  placement="top"
                  content="Slots for canceled / failed runs can automatically be freed by configuring a run monitoring setting."
                >
                  <Icon name="info" color={Colors.accentGray()} />
                </Tooltip>
              ) : null}
            </Box>
          </Link>
        ) : (
          <Mono>{titleForRun({id: step.runId})}</Mono>
        )}
      </td>
      <td>
        <Mono>{step.stepKey}</Mono>
      </td>
      <td>
        {step.assignedTimestamp ? (
          <TimeElapsed startUnix={step.assignedTimestamp} endUnix={null} />
        ) : (
          '-'
        )}
      </td>
      <td>
        {step.enqueuedTimestamp ? (
          <TimeElapsed startUnix={step.enqueuedTimestamp} endUnix={null} />
        ) : (
          '-'
        )}
      </td>
      <td>{step.priority}</td>
      <td>
        <ConcurrencyActionMenu pendingStep={step} onUpdate={onUpdate} />
      </td>
    </tr>
  );
};

const CONCURRENCY_STEP_FRAGMENT = gql`
  fragment ConcurrencyStepFragment on PendingConcurrencyStep {
    runId
    stepKey
    enqueuedTimestamp
    assignedTimestamp
    priority
  }
`;
const CONCURRENCY_LIMIT_FRAGMENT = gql`
  fragment ConcurrencyLimitFragment on ConcurrencyKeyInfo {
    concurrencyKey
    slotCount
    claimedSlots {
      runId
      stepKey
    }
    pendingSteps {
      ...ConcurrencyStepFragment
    }
  }
  ${CONCURRENCY_STEP_FRAGMENT}
`;
const RUN_QUEUE_CONFIG_FRAGMENT = gql`
  fragment RunQueueConfigFragment on RunQueueConfig {
    maxConcurrentRuns
    tagConcurrencyLimitsYaml
  }
`;

export const INSTANCE_CONCURRENCY_LIMITS_QUERY = gql`
  query InstanceConcurrencyLimitsQuery {
    instance {
      id
      info
      supportsConcurrencyLimits
      runQueuingSupported
      runQueueConfig {
        ...RunQueueConfigFragment
      }
      minConcurrencyLimitValue
      maxConcurrencyLimitValue
      concurrencyLimits {
        concurrencyKey
      }
    }
  }

  ${RUN_QUEUE_CONFIG_FRAGMENT}
`;

const SET_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
  }
`;

const DELETE_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation DeleteConcurrencyLimit($concurrencyKey: String!) {
    deleteConcurrencyLimit(concurrencyKey: $concurrencyKey)
  }
`;

export const FREE_CONCURRENCY_SLOTS_MUTATION = gql`
  mutation FreeConcurrencySlots($runId: String!, $stepKey: String) {
    freeConcurrencySlots(runId: $runId, stepKey: $stepKey)
  }
`;

const CONCURRENCY_KEY_DETAILS_QUERY = gql`
  query ConcurrencyKeyDetailsQuery($concurrencyKey: String!) {
    instance {
      id
      concurrencyLimit(concurrencyKey: $concurrencyKey) {
        ...ConcurrencyLimitFragment
      }
    }
  }
  ${CONCURRENCY_LIMIT_FRAGMENT}
`;

const RUNS_FOR_CONCURRENCY_KEY_QUERY = gql`
  query RunsForConcurrencyKeyQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on Runs {
        results {
          id
          status
        }
      }
    }
  }
`;
