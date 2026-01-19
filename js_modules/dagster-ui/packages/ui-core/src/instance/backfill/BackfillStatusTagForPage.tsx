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
    if (!error) {
      return <Tag intent="danger">{status}</Tag>;
    }

    const onClick = () =>
      error && showCustomAlert({title: '错误', body: <PythonErrorInfo error={error} />});

    return (
      <Box margin={{bottom: 12}} flex={{gap: 8}}>
        <TagButton onClick={onClick}>
          <Tag intent="danger">{status}</Tag>
        </TagButton>
        <ButtonLink onClick={onClick}>查看错误</ButtonLink>
      </Box>
    );
  }

  switch (status) {
    case BulkActionStatus.REQUESTED:
      return <Tag>进行中</Tag>;

    case BulkActionStatus.CANCELING:
      return errorState('取消中');
    case BulkActionStatus.CANCELED:
      return errorState('已取消');
    case BulkActionStatus.FAILED:
      return errorState('失败');
    case BulkActionStatus.FAILING:
      return errorState('失败中');
    case BulkActionStatus.COMPLETED:
      return <Tag intent="success">已完成</Tag>;
    case BulkActionStatus.COMPLETED_SUCCESS:
      return <Tag intent="success">成功</Tag>;
    case BulkActionStatus.COMPLETED_FAILED:
      return errorState('失败');
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
