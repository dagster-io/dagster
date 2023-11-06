import {gql, useQuery, useMutation} from '@apollo/client';
import {
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
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Redirect} from 'react-router-dom';

import {showSharedToaster} from '../app/DomUtils';
import {useFeatureFlags} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {doneStatuses} from '../runs/RunStatuses';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {RunTableRunFragment} from '../runs/types/RunTable.types';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  ConcurrencyLimitFragment,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
  RunsForConcurrencyKeyQuery,
  RunsForConcurrencyKeyQueryVariables,
  FreeConcurrencySlotsForRunMutation,
  FreeConcurrencySlotsForRunMutationVariables,
} from './types/InstanceConcurrency.types';

const RUNS_LIMIT = 25;

const InstanceConcurrencyPage = React.memo(() => {
  useTrackPageView();
  useDocumentTitle('Concurrency');
  const {flagInstanceConcurrencyLimits} = useFeatureFlags();

  const {pageTitle} = React.useContext(InstancePageContext);
  const queryResult = useQuery<
    InstanceConcurrencyLimitsQuery,
    InstanceConcurrencyLimitsQueryVariables
  >(INSTANCE_CONCURRENCY_LIMITS_QUERY, {
    notifyOnNetworkStatusChange: true,
  });

  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data} = queryResult;

  const content = data ? (
    flagInstanceConcurrencyLimits ? (
      <ConcurrencyLimits
        instanceConfig={data.instance.info}
        limits={data.instance.concurrencyLimits}
        hasSupport={data.instance.supportsConcurrencyLimits}
        refetch={queryResult.refetch}
      />
    ) : (
      <Redirect to="/config" />
    )
  ) : (
    <Box padding={{vertical: 64}}>
      <Spinner purpose="section" />
    </Box>
  );

  return (
    <Page>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="concurrency" refreshState={refreshState} />}
      />
      {content}
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

export const ConcurrencyLimits = ({
  instanceConfig,
  hasSupport,
  limits,
  refetch,
}: {
  limits: ConcurrencyLimitFragment[];
  refetch: () => void;
  instanceConfig?: string | null;
  hasSupport?: boolean;
}) => {
  const [action, setAction] = React.useState<DialogAction>();
  const [selectedRuns, setSelectedRuns] = React.useState<string[] | undefined>(undefined);
  const [selectedKey, setSelectedKey] = React.useState<string | undefined>(undefined);
  const onRunsDialogClose = React.useCallback(() => {
    setSelectedRuns(undefined);
    setSelectedKey(undefined);
  }, [setSelectedKey, setSelectedRuns]);

  const limitsByKey = Object.fromEntries(
    limits.map(({concurrencyKey, slotCount}) => [concurrencyKey, slotCount]),
  );

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
    );
  } else if (hasSupport === false) {
    return (
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
    );
  }

  return (
    <>
      <Box>
        <Box flex={{justifyContent: 'flex-end'}} padding={16}>
          <Button intent="primary" icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
            Add concurrency limit
          </Button>
        </Box>
        {limits.length === 0 ? (
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
        ) : (
          <Table>
            <thead>
              <tr>
                <th style={{width: '260px'}}>Concurrency key</th>
                <th style={{width: '20%'}}>Occupied slots</th>
                <th style={{width: '20%'}}>Total slots</th>
                <th>Active runs</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {limits.map((limit) => (
                <tr key={limit.concurrencyKey}>
                  <td>{limit.concurrencyKey}</td>
                  <td>{limit.activeSlotCount}</td>
                  <td>{limit.slotCount}</td>
                  <td>
                    {limit.activeRunIds.length === 0 ? (
                      <>&mdash;</>
                    ) : (
                      <Tag intent="primary" interactive>
                        <ButtonLink
                          onClick={() => {
                            setSelectedKey(limit.concurrencyKey);
                            setSelectedRuns(limit.activeRunIds);
                          }}
                        >
                          {limit.activeRunIds.length}{' '}
                          {limit.activeRunIds.length === 1 ? 'run' : 'runs'}
                        </ButtonLink>
                      </Tag>
                    )}
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
      </Box>
      <AddConcurrencyLimitDialog
        open={action?.actionType === 'add'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
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
      />
      <ConcurrencyRunsDialog
        title={
          <span>
            Active runs for <strong>{selectedKey}</strong>
          </span>
        }
        onClose={onRunsDialogClose}
        runIds={selectedRuns}
      />
    </>
  );
};

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

const isValidLimit = (concurrencyLimit?: string) => {
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
  return value > 0 && value < 1000;
};

const AddConcurrencyLimitDialog = ({
  open,
  onClose,
  onComplete,
}: {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
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
        <Box margin={{bottom: 4}}>Concurrency limit (1-1000):</Box>
        <Box>
          <TextInput
            value={limitInput || ''}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder="1 - 1000"
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
          disabled={!isValidLimit(limitInput.trim()) || !keyInput || isSubmitting}
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
}: {
  concurrencyKey: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
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
        <Box margin={{bottom: 4}}>Concurrency limit (1-1000):</Box>
        <Box>
          <TextInput
            value={limitInput || ''}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder="1 - 1000"
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
          <Button intent="primary" onClick={save} disabled={!isValidLimit(limitInput.trim())}>
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

  const [setConcurrencyLimit] = useMutation<
    SetConcurrencyLimitMutation,
    SetConcurrencyLimitMutationVariables
  >(SET_CONCURRENCY_LIMIT_MUTATION);

  const save = async () => {
    setIsSubmitting(true);
    await setConcurrencyLimit({
      variables: {concurrencyKey, limit: 0},
    });
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

const ConcurrencyRunsDialog = ({
  runIds,
  onClose,
  title,
}: {
  runIds?: string[];
  title: string | React.ReactNode;
  onClose: () => void;
}) => {
  const {data} = useQuery<RunsForConcurrencyKeyQuery, RunsForConcurrencyKeyQueryVariables>(
    RUNS_FOR_CONCURRENCY_KEY_QUERY,
    {
      variables: {
        limit: RUNS_LIMIT,
        filter: {
          runIds: runIds || [],
        },
      },
      skip: !runIds || !runIds.length,
    },
  );

  const [freeSlots] = useMutation<
    FreeConcurrencySlotsForRunMutation,
    FreeConcurrencySlotsForRunMutationVariables
  >(FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION);

  const freeSlotsActionMenuItem = React.useCallback(
    (run: RunTableRunFragment) => {
      return doneStatuses.has(run.status)
        ? [
            <MenuItem
              key="free-concurrency-slots"
              icon="status"
              text="Free concurrency slots for run"
              onClick={async () => {
                const resp = await freeSlots({variables: {runId: run.id}});
                if (resp.data?.freeConcurrencySlotsForRun) {
                  await showSharedToaster({
                    intent: 'success',
                    icon: 'copy_to_clipboard_done',
                    message: 'Freed concurrency slots',
                  });
                }
                onClose();
              }}
            />,
          ]
        : [];
    },
    [freeSlots, onClose],
  );

  return (
    <Dialog
      isOpen={!!runIds && runIds.length > 0}
      title={title}
      onClose={onClose}
      style={{minWidth: '400px', maxWidth: 'calc(100% - 40px)', width: 'fit-content'}}
    >
      <Box padding={{vertical: 16}}>
        {!data ? (
          <Box padding={{vertical: 64}}>
            <Spinner purpose="section" />
          </Box>
        ) : data.pipelineRunsOrError.__typename === 'Runs' ? (
          <div style={{overflow: 'auto'}}>
            <RunTable
              runs={data.pipelineRunsOrError.results}
              additionalActionsForRun={freeSlotsActionMenuItem}
            />
          </div>
        ) : (
          <Box padding={{vertical: 64}}>
            <NonIdealState
              icon="error"
              title="Query Error"
              description={
                data.pipelineRunsOrError.__typename === 'PythonError'
                  ? data.pipelineRunsOrError.message
                  : 'There was a problem querying for these runs.'
              }
            />
            ;
          </Box>
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

export const CONCURRENCY_LIMIT_FRAGMENT = gql`
  fragment ConcurrencyLimitFragment on ConcurrencyKeyInfo {
    concurrencyKey
    slotCount
    activeRunIds
    activeSlotCount
  }
`;

export const INSTANCE_CONCURRENCY_LIMITS_QUERY = gql`
  query InstanceConcurrencyLimitsQuery {
    instance {
      id
      info
      supportsConcurrencyLimits
      concurrencyLimits {
        ...ConcurrencyLimitFragment
      }
    }
  }

  ${CONCURRENCY_LIMIT_FRAGMENT}
`;

const SET_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
  }
`;

export const FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION = gql`
  mutation FreeConcurrencySlotsForRun($runId: String!) {
    freeConcurrencySlotsForRun(runId: $runId)
  }
`;

const RUNS_FOR_CONCURRENCY_KEY_QUERY = gql`
  query RunsForConcurrencyKeyQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on Runs {
        results {
          id
          ... on PipelineRun {
            ...RunTableRunFragment
          }
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
