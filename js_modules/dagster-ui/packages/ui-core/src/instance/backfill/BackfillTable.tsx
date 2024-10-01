import {Table} from '@dagster-io/ui-components';
import {useState} from 'react';

import {BACKFILL_ACTIONS_BACKFILL_FRAGMENT} from './BackfillFragments';
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
  const [partitionsRequestedBackfill, setPartitionsRequestedBackfill] =
    useState<BackfillTableFragment>();

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th>Backfill ID</th>
            <th>Created</th>
            {showBackfillTarget ? <th>Backfill target</th> : null}
            <th>Requested</th>
            <th>Launched by</th>
            <th>Backfill status</th>
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
        backfill={partitionsRequestedBackfill}
        onClose={() => setPartitionsRequestedBackfill(undefined)}
      />
    </>
  );
};

export const PARTITION_SET_FOR_BACKFILL_TABLE_FRAGMENT = gql`
  fragment PartitionSetForBackfillTableFragment on PartitionSet {
    id
    name
    mode
    pipelineName
    repositoryOrigin {
      id
      repositoryName
      repositoryLocationName
    }
  }
`;

export const BACKFILL_TABLE_FRAGMENT = gql`
  fragment BackfillTableFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
    isValidSerialization
    partitionNames
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
