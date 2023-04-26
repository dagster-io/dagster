import {gql, useQuery, useMutation} from '@apollo/client';
import {
  Box,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Menu,
  MenuItem,
  Mono,
  Popover,
  Spinner,
  Subheading,
  Table,
  Tag,
  TextInput,
  Button,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {titleForRun} from '../runs/RunUtils';

import {
  InstanceConcurrencyLimitsQuery,
  InstanceConcurrencyLimitsQueryVariables,
  SetConcurrencyLimitMutation,
  SetConcurrencyLimitMutationVariables,
} from './types/ConcurrencyLimits.types';

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

export const ConcurrencyLimits = () => {
  const queryResult = useQuery<
    InstanceConcurrencyLimitsQuery,
    InstanceConcurrencyLimitsQueryVariables
  >(INSTANCE_CONCURRENCY_LIMITS_QUERY);
  const [action, setAction] = React.useState<DialogAction>();

  if (!queryResult.data) {
    return (
      <Box padding={{vertical: 64}}>
        <Spinner purpose="section" />
      </Box>
    );
  }

  const limitsByKey: {[key: string]: number} = {};
  queryResult.data.instance.concurrencyLimits.forEach((limit) => {
    limitsByKey[limit.concurrencyKey] = limit.limit;
  });

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
      <ConcurrencyLimitDialog
        open={!!action}
        onClose={() => setAction(undefined)}
        onComplete={queryResult.refetch}
        action={action}
      />
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
      >
        <Subheading>Concurrency limits</Subheading>
      </Box>
      <Box padding={24} border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}>
        <Table>
          <thead>
            <tr style={{border: `1px solid ${Colors.KeylineGray}`}}>
              <th style={{width: '260px'}}>Concurrency Key</th>
              <th style={{width: '20%'}}>Occupied slots</th>
              <th style={{width: '20%'}}>Total slots</th>
              <th>Active runs</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {queryResult.data?.instance.concurrencyLimits.map((limit) => (
              <tr key={limit.id}>
                <td>{limit.id}</td>
                <td>{limit.numActive}</td>
                <td>{limit.limit}</td>
                <td>
                  {limit.activeRunIds.length === 0 ? (
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
                    <TagButton onClick={() => {}}>
                      <Tag intent="primary" interactive>
                        {limit.activeRunIds.length} runs
                      </Tag>
                    </TagButton>
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
        <Box flex={{justifyContent: 'flex-end'}} padding={{vertical: 16}}>
          <Button onClick={() => onAdd()}>Add concurrency limit</Button>
        </Box>
      </Box>
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

interface DialogProps {
  action: DialogAction;
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const ConcurrencyLimitDialog = ({action, open, onClose, onComplete}: DialogProps) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [limitInput, setLimitInput] = React.useState(
    action?.actionType === 'edit' ? String(action.concurrencyLimit) : '',
  );
  const [keyInput, setKeyInput] = React.useState(
    action?.actionType === 'edit' || action?.actionType === 'delete' ? action?.concurrencyKey : '',
  );

  React.useEffect(() => {
    setLimitInput(action?.actionType === 'edit' ? String(action.concurrencyLimit) : '');
    setKeyInput(
      action?.actionType === 'edit' || action?.actionType === 'delete'
        ? action?.concurrencyKey
        : '',
    );
  }, [action]);

  const [setConcurrencyLimit] = useMutation<
    SetConcurrencyLimitMutation,
    SetConcurrencyLimitMutationVariables
  >(SET_CONCURRENCY_LIMIT_MUTATION);

  const save = async () => {
    if (!action) {
      return;
    }
    setIsSubmitting(true);
    const limit = action.actionType === 'delete' ? 0 : parseInt(limitInput!);
    const concurrencyKey = action.actionType === 'add' ? keyInput : action.concurrencyKey;
    await setConcurrencyLimit({
      variables: {concurrencyKey, limit},
    });
    setIsSubmitting(false);
    onComplete();
    onClose();
  };

  const isValidLimit = React.useCallback((concurrencyLimit?: string) => {
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
  }, []);

  let title;
  switch (action?.actionType) {
    case 'delete':
      title = (
        <>
          Delete <Mono>{action.concurrencyKey}</Mono>
        </>
      );
      break;
    case 'edit':
      title = (
        <>
          Edit <Mono>{action.concurrencyKey}</Mono>
        </>
      );
      break;
    case 'add':
      title = 'Add limit';
      break;
    default:
      title = '';
  }

  return (
    <Dialog isOpen={open} title={title} onClose={onClose}>
      {action?.actionType === 'add' ? (
        <>
          <DialogBody>
            <Box flex={{justifyContent: 'flex-start'}}>
              <TextInput
                value={keyInput || ''}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="Concurrency key"
              />
              <TextInput
                style={{marginLeft: 8}}
                value={limitInput || ''}
                onChange={(e) => setLimitInput(e.target.value)}
                placeholder="Concurrency limit"
              />
            </Box>
          </DialogBody>
          <DialogFooter>
            <Button intent="none" onClick={onClose}>
              Close
            </Button>
            {isSubmitting ? (
              <Button intent="primary" disabled>
                Adding...
              </Button>
            ) : (
              <Button
                intent="primary"
                onClick={save}
                disabled={!isValidLimit(limitInput) || !keyInput}
              >
                Add limit
              </Button>
            )}
          </DialogFooter>
        </>
      ) : action?.actionType === 'edit' ? (
        <>
          <DialogBody>
            <Box flex={{justifyContent: 'flex-start'}}>
              <TextInput
                value={action.concurrencyKey}
                disabled={true}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="Concurrency key"
              />
              <TextInput
                style={{marginLeft: 8}}
                value={limitInput || ''}
                onChange={(e) => setLimitInput(e.target.value)}
                placeholder="Concurrency limit"
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
                disabled={!isValidLimit(limitInput) || !keyInput}
              >
                Update limit
              </Button>
            )}
          </DialogFooter>
        </>
      ) : action?.actionType === 'delete' ? (
        <>
          <DialogBody>
            <Box flex={{justifyContent: 'flex-start'}}>
              Delete concurrency limit {action.concurrencyKey}?
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
        </>
      ) : null}
    </Dialog>
  );
};

const INSTANCE_CONCURRENCY_LIMITS_QUERY = gql`
  query InstanceConcurrencyLimitsQuery {
    instance {
      id
      concurrencyLimits {
        __typename
        id
        concurrencyKey
        limit
        activeRunIds
        numActive
      }
    }
  }
`;

const SET_CONCURRENCY_LIMIT_MUTATION = gql`
  mutation SetConcurrencyLimit($concurrencyKey: String!, $limit: Int!) {
    setConcurrencyLimit(concurrencyKey: $concurrencyKey, limit: $limit)
  }
`;

const TagButton = styled.button`
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus {
    outline: none;
  }
`;
