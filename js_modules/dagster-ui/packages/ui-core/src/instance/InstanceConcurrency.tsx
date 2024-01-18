import {gql, useQuery, useMutation} from '@apollo/client';
import {
  Subheading,
  MetadataTableWIP,
  StyledRawCodeMirror,
  PageHeader,
  Heading,
  Box,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Mono,
  Popover,
  Spinner,
  ButtonLink,
  Table,
  Tag,
  TextInput,
  Button,
  NonIdealState,
  Page,
  Tooltip,
  colorAccentGray,
  colorTextLight,
  colorBackgroundYellow,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {showSharedToaster} from '../app/DomUtils';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {COMMON_COLLATOR} from '../app/Util';
import {useTrackPageView} from '../app/analytics';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunStatusDot} from '../runs/RunStatusDots';
import {failedStatuses} from '../runs/RunStatuses';
import {titleForRun} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {
  ConcurrencyKeyDetailsQuery,
  ConcurrencyKeyDetailsQueryVariables,
  ConcurrencyLimitFragment,
  ConcurrencyStepFragment,
  FreeConcurrencySlotsMutation,
  FreeConcurrencySlotsMutationVariables,
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  RunsForConcurrencyKeyQuery,
  RunsForConcurrencyKeyQueryVariables,
  RunQueueConfigFragment,
  DeleteConcurrencyLimitMutation,
  DeleteConcurrencyLimitMutationVariables,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/InstanceConcurrency.types';

const DEFAULT_MIN_VALUE = 1;
const DEFAULT_MAX_VALUE = 1000;

const InstanceConcurrencyPage = React.memo(() => {
  useTrackPageView();
  useDocumentTitle('Concurrency');
  const {pageTitle} = React.useContext(InstancePageContext);
  const queryResult = useQuery<
    InstanceConcurrencyLimitsQuery,
    InstanceConcurrencyLimitsQueryVariables
  >(INSTANCE_CONCURRENCY_LIMITS_QUERY, {
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;

  return (
    <Page>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="concurrency" refreshState={refreshState} />}
      />
      {data ? (
        <>
          <Box margin={{bottom: 64}}>
            <RunConcurrencyContent
              hasRunQueue={!!data?.instance.runQueuingSupported}
              runQueueConfig={data?.instance.runQueueConfig}
            />
          </Box>
          <ConcurrencyLimits
            instanceConfig={data.instance.info}
            limits={data.instance.concurrencyLimits}
            hasSupport={data.instance.supportsConcurrencyLimits}
            refetch={queryResult.refetch}
            minValue={data.instance.minConcurrencyLimitValue}
            maxValue={data.instance.maxConcurrencyLimitValue}
          />
        </>
      ) : (
        <Box padding={{vertical: 64}}>
          <Spinner purpose="section" />
        </Box>
      )}
    </Page>
  );
});

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
      concurrencyLimit: number;
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
}: {
  hasRunQueue: boolean;
  runQueueConfig: RunQueueConfigFragment | null | undefined;
  onEdit?: () => void;
}) => {
  if (!hasRunQueue) {
    return (
      <>
        <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
          <Subheading>Run concurrency</Subheading>
        </Box>
        <div>
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
        </div>
      </>
    );
  }

  const info_content = (
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
          <td>
            <Mono>{runQueueConfig.maxConcurrentRuns}</Mono>
          </td>
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
      <RunConcurrencyLimitHeader onEdit={onEdit} />
      {info_content}
      {settings_content}
    </>
  );
};

const RunConcurrencyLimitHeader = ({onEdit}: {onEdit?: () => void}) => (
  <Box
    flex={{justifyContent: 'space-between', alignItems: 'center'}}
    padding={{vertical: 16, horizontal: 24}}
    border="bottom"
  >
    <Subheading>Run concurrency</Subheading>
    {onEdit ? (
      <Button icon={<Icon name="edit" />} onClick={() => onEdit()}>
        Edit configuration
      </Button>
    ) : (
      <span />
    )}
  </Box>
);

export const ConcurrencyLimits = ({
  instanceConfig,
  hasSupport,
  limits,
  refetch,
  minValue,
  maxValue,
}: {
  limits: ConcurrencyLimitFragment[];
  refetch: () => void;
  instanceConfig?: string | null;
  hasSupport?: boolean;
  maxValue?: number;
  minValue?: number;
}) => {
  const [action, setAction] = React.useState<DialogAction>();
  const [selectedKey, setSelectedKey] = React.useState<string | undefined>(undefined);
  const onConcurrencyStepsDialogClose = React.useCallback(() => {
    setSelectedKey(undefined);
  }, [setSelectedKey]);

  const limitsByKey = Object.fromEntries(
    limits.map(({concurrencyKey, slotCount}) => [concurrencyKey, slotCount]),
  );

  const sortedLimits = React.useMemo(() => {
    return [...limits].sort((a, b) => COMMON_COLLATOR.compare(a.concurrencyKey, b.concurrencyKey));
  }, [limits]);

  const onAdd = () => {
    setAction({actionType: 'add'});
  };
  const onEdit = (concurrencyKey: string) => {
    setAction({actionType: 'edit', concurrencyKey, concurrencyLimit: limitsByKey[concurrencyKey]!});
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
    <>
      <ConcurrencyLimitHeader onAdd={onAdd} />
      {limits.length === 0 ? (
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
        <Table>
          <thead>
            <tr>
              <th style={{width: '260px'}}>Concurrency key</th>
              <th style={{width: '20%'}}>Total slots</th>
              <th style={{width: '20%'}}>Assigned steps</th>
              <th style={{width: '20%'}}>Pending steps</th>
              <th style={{width: '20%'}}>All steps</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sortedLimits.map((limit) => (
              <tr key={limit.concurrencyKey}>
                <td>{limit.concurrencyKey}</td>
                <td>{limit.slotCount}</td>
                <td>{limit.pendingSteps.filter((x) => !!x.assignedTimestamp).length}</td>
                <td>{limit.pendingSteps.filter((x) => !x.assignedTimestamp).length}</td>
                <td>
                  <span style={{marginRight: 16}}>{limit.pendingSteps.length}</span>
                  <Tag intent="primary" interactive>
                    <ButtonLink
                      onClick={() => {
                        setSelectedKey(limit.concurrencyKey);
                      }}
                    >
                      View all
                    </ButtonLink>
                  </Tag>
                </td>
                <td>
                  <ConcurrencyLimitActionMenu
                    concurrencyKey={limit.concurrencyKey}
                    onEdit={onEdit}
                    onDelete={onDelete}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
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
    </>
  );
};

const ConcurrencyLimitHeader = ({onAdd}: {onAdd?: () => void}) => (
  <Box
    flex={{justifyContent: 'space-between', alignItems: 'center'}}
    padding={{vertical: 16, horizontal: 24}}
    border="top-and-bottom"
  >
    <Subheading>
      <Box flex={{alignItems: 'center', direction: 'row', gap: 8}}>
        <span>Global op/asset concurrency</span>
        <Tag>Experimental</Tag>
      </Box>
    </Subheading>
    {onAdd ? (
      <Button icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
        Add concurrency limit
      </Button>
    ) : null}
  </Box>
);

const ConcurrencyLimitActionMenu = ({
  concurrencyKey,
  onDelete,
  onEdit,
}: {
  concurrencyKey: string;
  onEdit: (key: string) => void;
  onDelete: (key: string) => void;
}) => {
  return (
    <Popover
      content={
        <Menu>
          <MenuItem icon="edit" text="Edit" onClick={() => onEdit(concurrencyKey)} />
          <MenuItem
            icon="delete"
            intent="danger"
            text="Delete"
            onClick={() => onDelete(concurrencyKey)}
          />
        </Menu>
      }
      position="bottom-left"
    >
      <Button icon={<Icon name="expand_more" />} />
    </Popover>
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
  concurrencyKey?: string;
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
              <Icon name="info" color={colorAccentGray()} />
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
                style={{color: colorTextLight()}}
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
      <tbody style={{backgroundColor: colorBackgroundYellow()}}>
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
                  <Icon name="info" color={colorAccentGray()} />
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

export const CONCURRENCY_STEP_FRAGMENT = gql`
  fragment ConcurrencyStepFragment on PendingConcurrencyStep {
    runId
    stepKey
    enqueuedTimestamp
    assignedTimestamp
    priority
  }
`;
export const CONCURRENCY_LIMIT_FRAGMENT = gql`
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
export const RUN_QUEUE_CONFIG_FRAGMENT = gql`
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
        ...ConcurrencyLimitFragment
      }
    }
  }

  ${CONCURRENCY_LIMIT_FRAGMENT}
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
