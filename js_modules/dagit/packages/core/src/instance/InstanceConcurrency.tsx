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
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {titleForRun} from '../runs/RunUtils';

import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  ConcurrencyLimitFragment,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/InstanceConcurrency.types';

const RUNS_LIMIT = 25;

const InstanceConcurrencyPage = React.memo(() => {
  useTrackPageView();
  useDocumentTitle('Configuration');
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

  if (!data) {
    return (
      <Box padding={{vertical: 64}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  const limits = data.instance.concurrencyLimits;
  return (
    <>
      <PageHeader
        title={<Heading>{pageTitle}</Heading>}
        tabs={<InstanceTabs tab="concurrency" refreshState={refreshState} />}
      />
      {flagInstanceConcurrencyLimits ? (
        <ConcurrencyLimits limits={limits} refetch={queryResult.refetch} />
      ) : null}
    </>
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

const ConcurrencyLimits: React.FC<{
  limits: ConcurrencyLimitFragment[];
  refetch: () => void;
}> = ({limits, refetch}) => {
  const [action, setAction] = React.useState<DialogAction>();
  const [selectedRuns, setSelectedRuns] = React.useState<string[] | undefined>(undefined);
  const [selectedKey, setSelectedKey] = React.useState<string | undefined>(undefined);

  const limitsByKey = Object.fromEntries(
    limits.map(({concurrencyKey, slotCount}) => [concurrencyKey, slotCount]),
  );

  const onAdd = () => {
    setAction({actionType: 'add'});
  };
  const onEdit = (concurrencyKey: string) => {
    setAction({actionType: 'edit', concurrencyKey, concurrencyLimit: limitsByKey[concurrencyKey]});
  };
  const onDelete = (concurrencyKey: string) => {
    setAction({actionType: 'delete', concurrencyKey});
  };

  return (
    <>
      <Box>
        <Box flex={{justifyContent: 'flex-end'}} padding={16}>
          <Button intent="primary" icon={<Icon name="add_circle" />} onClick={() => onAdd()}>
            Add concurrency limit
          </Button>
        </Box>
        {limits.length === 0 ? (
          <Box padding={{vertical: 64}} flex={{justifyContent: 'center'}}>
            No concurrency limits have been configured for this instance.&nbsp;
            <ButtonLink onClick={() => onAdd()}>Add a concurrency limit</ButtonLink>.
          </Box>
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
                    {limit.activeRunIds.length === 0 && false ? (
                      <>&mdash;</>
                    ) : limit.activeRunIds.length === 1 ? (
                      <Tag intent="primary">
                        <Link to={`/runs/${limit.activeRunIds[0]}`}>
                          <Mono style={{fontSize: '14px'}}>
                            {titleForRun({id: limit.activeRunIds[0]})}
                          </Mono>
                        </Link>
                      </Tag>
                    ) : (
                      <Tag intent="primary" interactive>
                        <ButtonLink
                          onClick={() => {
                            setSelectedKey(limit.concurrencyKey);
                            setSelectedRuns(limit.activeRunIds);
                          }}
                        >
                          {limit.activeRunIds.length} runs
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
        open={!!action && action.actionType === 'add'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
      />
      <DeleteConcurrencyLimitDialog
        concurrencyKey={action && action.actionType === 'delete' ? action.concurrencyKey : ''}
        open={!!action && action.actionType === 'delete'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
      />
      <EditConcurrencyLimitDialog
        open={!!action && action.actionType === 'edit'}
        onClose={() => setAction(undefined)}
        onComplete={refetch}
        concurrencyKey={action && action.actionType === 'edit' ? action.concurrencyKey : ''}
      />
      <ConcurrencyRunsDialog
        title={
          <span>
            Active runs for <strong>{selectedKey}</strong>
          </span>
        }
        onClose={() => {
          setSelectedRuns(undefined);
          setSelectedKey(undefined);
        }}
        runIds={selectedRuns}
      />
    </>
  );
};

const ConcurrencyLimitActionMenu: React.FC<{
  concurrencyKey: string;
  onEdit: (key: string) => void;
  onDelete: (key: string) => void;
}> = ({concurrencyKey, onDelete, onEdit}) => {
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

const AddConcurrencyLimitDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}> = ({open, onClose, onComplete}) => {
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
      variables: {concurrencyKey: keyInput, limit: parseInt(limitInput!.trim())},
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
        <Box margin={{bottom: 4}}>Concurrency limit:</Box>
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
          disabled={!isValidLimit(limitInput.trim()) || !keyInput}
        >
          {isSubmitting ? 'Adding...' : 'Add limit'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const EditConcurrencyLimitDialog: React.FC<{
  concurrencyKey: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}> = ({concurrencyKey, open, onClose, onComplete}) => {
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
        <Box margin={{bottom: 4}}>Concurrency limit:</Box>
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

const DeleteConcurrencyLimitDialog: React.FC<{
  concurrencyKey: string;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}> = ({concurrencyKey, open, onClose, onComplete}) => {
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
        <Box flex={{justifyContent: 'flex-start'}}>
          Delete concurrency limit&nbsp;<strong>{concurrencyKey}</strong>?
        </Box>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
        {isSubmitting ? (
          <Button intent="primary" disabled>
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

const ConcurrencyRunsDialog: React.FC<{
  runIds?: string[];
  title: string | React.ReactNode;
  onClose: () => void;
}> = ({runIds, onClose, title}) => {
  const {data} = useQuery(RUNS_FOR_CONCURRENCY_KEY_QUERY, {
    variables: {
      limit: RUNS_LIMIT,
      filter: {
        runIds: runIds || [],
      },
    },
    skip: !runIds,
  });

  if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
    return null;
  }

  const runs = data?.pipelineRunsOrError.results;

  return (
    <Dialog
      isOpen={!!runIds}
      title={title}
      onClose={onClose}
      style={{width: '60%', minWidth: '400px'}}
    >
      <DialogBody>
        <RunTable runs={runs} />
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

const CONCURRENCY_LIMIT_FRAGMENT = gql`
  fragment ConcurrencyLimitFragment on ConcurrencyKeyInfo {
    concurrencyKey
    slotCount
    activeRunIds
    activeSlotCount
  }
`;

const INSTANCE_CONCURRENCY_LIMITS_QUERY = gql`
  query InstanceConcurrencyLimitsQuery {
    instance {
      id
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
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
`;
