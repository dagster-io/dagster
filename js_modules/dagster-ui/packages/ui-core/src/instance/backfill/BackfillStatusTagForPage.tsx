import {Box, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {showCustomAlert} from '../../app/CustomAlertProvider';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {PythonErrorFragment} from '../../app/types/PythonErrorFragment.types';
import {BulkActionStatus} from '../../graphql/types';

type BackfillState = {
  status: BulkActionStatus;
  error: PythonErrorFragment | null;
  blockedReason: string | null;
};

export const BackfillStatusTagForPage = ({backfill}: {backfill: BackfillState}) => {
  const {status, error, blockedReason} = backfill;
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

  function blockedState(status: string, blockedReason: string) {
    return (
      <Box margin={{bottom: 12}}>
        <TagButton onClick={() => showCustomAlert({title: 'Warning', body: blockedReason})}>
          <Tag intent="warning">{status}</Tag>
        </TagButton>
      </Box>
    );
  }

  switch (status) {
    case BulkActionStatus.REQUESTED:
      if (blockedReason) {
        return blockedState('Blocked', blockedReason);
      } else {
        return <Tag>In progress</Tag>;
      }
    case BulkActionStatus.CANCELING:
      return errorState('Canceling');
    case BulkActionStatus.CANCELED:
      return errorState('Canceled');
    case BulkActionStatus.FAILED:
      return errorState('Failed');
    case BulkActionStatus.COMPLETED:
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
