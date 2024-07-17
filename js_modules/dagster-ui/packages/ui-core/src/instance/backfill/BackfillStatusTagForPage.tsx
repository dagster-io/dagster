import {Box, Tag} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {RunStatus} from '../../graphql/types';

type BackfillState = {
  status: RunStatus;
  error: PythonErrorFragment | null;
};

export const BackfillStatusTagForPage = ({backfill}: {backfill: BackfillState}) => {
  const {status, error} = backfill;
  function errorState(status: string) {
    return (
      <Box margin={{bottom: 12}}>
        <TagButton
          onClick={() =>
            error && showCustomAlert({title: 'Error', body: <PythonErrorInfo error={error} />})
          }
        >
          <Tag intent="danger">{status}</Tag>
        </TagButton>
      </Box>
    );
  }

  switch (status) {
    case RunStatus.STARTED:
      return <Tag>In progress</Tag>;

    case RunStatus.CANCELING:
      return errorState('Canceling');
    case RunStatus.CANCELED:
      return errorState('Canceled');
    case RunStatus.FAILURE:
      return errorState('Failed');
    case RunStatus.SUCCESS:
      return <Tag intent="success">Completed</Tag>;
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
