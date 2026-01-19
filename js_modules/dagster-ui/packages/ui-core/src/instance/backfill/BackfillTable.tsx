import {Table} from '@dagster-io/ui-components';
import {useState} from 'react';

import {
  BACKFILL_ACTIONS_BACKFILL_FRAGMENT,
  PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT,
} from './BackfillFragments';
import {BackfillPartitionsRequestedDialog} from './BackfillPartitionsRequestedDialog';
import {BackfillRow} from './BackfillRow';
import {BackfillTableFragment} from './types/BackfillTable.types';
import {gql} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';

export const BackfillTable = ({
  showBackfillTarget = true,
  allPartitions,
  backfills,
  refetch,
}: {
  allPartitions?: string[];
  backfills: BackfillTableFragment[];
  refetch: () => void;
  showBackfillTarget?: boolean;
}) => {
  const [partitionsRequestedBackfill, setPartitionsRequestedBackfill] = useState<string>();

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th>回填 ID</th>
            <th>创建时间</th>
            {showBackfillTarget ? <th>回填目标</th> : null}
            <th>请求数</th>
            <th>发起人</th>
            <th>回填状态</th>
            <th style={{width: 80}} />
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill) => (
            <BackfillRow
              key={backfill.id}
              showBackfillTarget={showBackfillTarget}
              backfill={backfill}
              allPartitions={allPartitions}
              onShowPartitionsRequested={setPartitionsRequestedBackfill}
              refetch={refetch}
            />
          ))}
        </tbody>
      </Table>

      <BackfillPartitionsRequestedDialog
        backfillId={partitionsRequestedBackfill}
        onClose={() => setPartitionsRequestedBackfill(undefined)}
      />
    </>
  );
};

export const BACKFILL_TABLE_FRAGMENT = gql`
  fragment BackfillTableFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
    isValidSerialization
    numPartitions
    timestamp
    partitionSetName
    partitionSet {
      id
      ...PartitionSetForBackfillTableFragment
    }
    assetSelection {
      path
    }
    tags {
      key
      value
    }
    error {
      ...PythonErrorFragment
    }
    ...BackfillActionsBackfillFragment
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${BACKFILL_ACTIONS_BACKFILL_FRAGMENT}
  ${PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT}
`;
