import {Box, ButtonLink, Tag} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {BulkActionStatus} from '../../graphql/types';

type BackfillState = {
  status: BulkActionStatus;
  error: PythonErrorFragment | null;
};

export const BackfillStatusTagForPage = ({backfill}: {backfill: BackfillState}) => {
  const {status, error} = backfill;
  function errorState(status: string) {
    const onClick = () =>
      error && showCustomAlert({title: 'Error', body: <PythonErrorInfo error={error} />});

    return (
      <Box margin={{bottom: 12}} flex={{gap: 8}}>
        <TagButton onClick={onClick}>
          <Tag intent="danger">{status}</Tag>
        </TagButton>
        <ButtonLink onClick={onClick}>View error</ButtonLink>
      </Box>
    );
  }

  switch (status) {
    case BulkActionStatus.REQUESTED:
      return <Tag>In progress</Tag>;

    case BulkActionStatus.CANCELING:
      return errorState('Canceling');
    case BulkActionStatus.CANCELED:
      return errorState('Canceled');
    case BulkActionStatus.FAILED:
      return errorState('Failed');
    case BulkActionStatus.COMPLETED:
      return <Tag intent="success">Completed</Tag>;
    case BulkActionStatus.COMPLETED_SUCCESS:
      return <Tag intent="success">Succeeded</Tag>;
    case BulkActionStatus.COMPLETED_FAILED:
      return errorState('Failed');
    default:
      return <Tag>{status}</Tag>;
  }
};

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
