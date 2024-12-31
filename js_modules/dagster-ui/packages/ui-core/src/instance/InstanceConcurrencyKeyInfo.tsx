import {
  Box,
  Button,
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
  Popover,
  SpinnerWithText,
  Subheading,
  Table,
  TextInput,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link, useHistory} from 'react-router-dom';

import {gql, useMutation, useQuery} from '../apollo-client';
import {
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/InstanceConcurrency.types';
import {
  ConcurrencyKeyDetailsQuery,
  ConcurrencyKeyDetailsQueryVariables,
  ConcurrencyLimitFragment,
  ConcurrencyStepFragment,
  DeleteConcurrencyLimitMutation,
  DeleteConcurrencyLimitMutationVariables,
  FreeConcurrencySlotsMutation,
  FreeConcurrencySlotsMutationVariables,
  RunsForConcurrencyKeyQuery,
  RunsForConcurrencyKeyQueryVariables,
} from './types/InstanceConcurrencyKeyInfo.types';
import {showSharedToaster} from '../app/DomUtils';
import {useFeatureFlags} from '../app/Flags';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunStatusDot} from '../runs/RunStatusDots';
import {failedStatuses} from '../runs/RunStatuses';
import {titleForRun} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';

const DEFAULT_MIN_VALUE = 0;
const DEFAULT_MAX_VALUE = 1000;

export const InstanceConcurrencyKeyInfo = ({concurrencyKey}: {concurrencyKey: string}) => {
  useTrackPageView();
  useDocumentTitle(`Pool: ${concurrencyKey}`);
  const [showEdit, setShowEdit] = React.useState<boolean>();
  const [showDelete, setShowDelete] = React.useState<boolean>(false);
  const queryResult = useQuery<ConcurrencyKeyDetailsQuery, ConcurrencyKeyDetailsQueryVariables>(
    CONCURRENCY_KEY_DETAILS_QUERY,
    {
      variables: {concurrencyKey},
    },
  );
  const {data, refetch} = queryResult;
  const concurrencyLimit = data?.instance.concurrencyLimit;
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {flagPoolUI} = useFeatureFlags();
  const history = useHistory();
  const onDelete = () => {
    history.push('/deployment/concurrency');
    showSharedToaster({
      icon: 'trash',
      intent: 'success',
      message: flagPoolUI ? 'Deleted pool limit' : 'Deleted concurrency key',
    });
  };

  return (
    <>
      <div style={{overflowY: 'auto'}}>
        {concurrencyLimit ? (
          <Box>
            <Box
              padding={{vertical: 16, horizontal: 24}}
              flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
              border="bottom"
            >
              <Heading>
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                  <div>
                    <Link to="/deployment/concurrency">
                      {flagPoolUI ? 'Pools' : 'Concurrency keys'}
                    </Link>
                  </div>
                  <div>/</div>
                  <div>{concurrencyKey}</div>
                </Box>
              </Heading>
              <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                <QueryRefreshCountdown refreshState={refreshState} />
                <Popover
                  position="bottom-right"
                  content={
                    <Menu>
                      <MenuItem
                        icon="delete"
                        text="Delete"
                        intent="danger"
                        onClick={() => setShowDelete(true)}
                      />
                    </Menu>
                  }
                >
                  <Button icon={<Icon name="expand_more" />} />
                </Popover>
              </Box>
            </Box>
            <Box padding={{vertical: 16, horizontal: 24}}>
              <Subheading>{flagPoolUI ? 'Pool info' : 'Concurrency info'}</Subheading>
            </Box>
            <Box padding={{bottom: 24}}>
              <MetadataTableWIP style={{marginLeft: -1}}>
                <tbody>
                  {flagPoolUI ? (
                    <tr>
                      <td style={{verticalAlign: 'middle'}}>Granularity</td>
                      <td>Op</td>
                    </tr>
                  ) : null}
                  <tr>
                    <td style={{verticalAlign: 'middle'}}>Limit</td>
                    <td>
                      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
                        <div>
                          {concurrencyLimit.slotCount ? (
                            concurrencyLimit.slotCount
                          ) : concurrencyLimit.limit === null ? (
                            <>&mdash;</>
                          ) : (
                            concurrencyLimit.limit
                          )}
                        </div>
                        <Button icon={<Icon name="edit" />} onClick={() => setShowEdit(true)}>
                          Edit limit
                        </Button>
                      </Box>
                    </td>
                  </tr>
                </tbody>
              </MetadataTableWIP>
            </Box>
            <Box
              padding={{vertical: 16, horizontal: 24}}
              flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
            >
              <Subheading>In progress</Subheading>
            </Box>
            <Box style={{marginLeft: -1}}>
              <PendingStepsTable keyInfo={concurrencyLimit} refresh={refetch} />
            </Box>
          </Box>
        ) : (
          <Box padding={{vertical: 64}}>
            <SpinnerWithText label="Loading…" />
          </Box>
        )}
      </div>
      <EditConcurrencyLimitDialog
        concurrencyKey={concurrencyKey}
        open={!!showEdit}
        onClose={() => setShowEdit(false)}
        onComplete={refetch}
        minValue={data?.instance.minConcurrencyLimitValue || DEFAULT_MIN_VALUE}
        maxValue={data?.instance.maxConcurrencyLimitValue || DEFAULT_MAX_VALUE}
      />
      <DeleteConcurrencyLimitDialog
        concurrencyKey={concurrencyKey}
        open={!!showDelete}
        onClose={() => setShowDelete(false)}
        onComplete={onDelete}
      />
    </>
  );
};

export const isValidLimit = (
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

  const {flagPoolUI} = useFeatureFlags();
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
        <Box margin={{bottom: 4}}>{flagPoolUI ? 'Pool' : 'Concurrency key'}:</Box>
        <Box margin={{bottom: 16}}>
          <strong>{concurrencyKey}</strong>
        </Box>
        <Box margin={{bottom: 4}}>
          {flagPoolUI ? 'Pool' : 'Concurrency'} limit ({minValue}-{maxValue}):
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
            Updating…
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
        <Button onClick={onClose}>Close</Button>
        <Button intent="danger" disabled={isSubmitting} onClick={save}>
          {isSubmitting ? 'Deleting…' : 'Delete limit'}
        </Button>
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

const PendingStepsTable = ({
  keyInfo,
  refresh,
}: {
  keyInfo: ConcurrencyLimitFragment;
  refresh: () => void;
}) => {
  const runIds = [...new Set(keyInfo.pendingSteps.map((step) => step.runId))];
  const {flagPoolUI} = useFeatureFlags();
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

  const emptyErrorMessage = flagPoolUI
    ? 'There are no active or pending steps for this pool.'
    : 'There are no active or pending steps for this concurrency key.';
  if (!steps.length) {
    return (
      <NonIdealState icon="no-results" title="No active steps" description={emptyErrorMessage} />
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
    limit
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

export const CONCURRENCY_KEY_DETAILS_QUERY = gql`
  query ConcurrencyKeyDetailsQuery($concurrencyKey: String!) {
    instance {
      id
      minConcurrencyLimitValue
      maxConcurrencyLimitValue
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
