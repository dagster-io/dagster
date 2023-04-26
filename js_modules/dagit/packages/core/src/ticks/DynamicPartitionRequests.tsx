import {Box, Colors, Icon, Subheading, Table, Tag} from '@dagster-io/ui';
import React from 'react';

import {PartitionRequestType} from '../graphql/types';

import {DynamicPartitionRequestFragment} from './types/SensorDryRunDialog.types';

export function DynamicPartitionRequests({
  requests,
}: {
  requests: DynamicPartitionRequestFragment[];
}) {
  const rows = React.useMemo(() => {
    if (!requests.length) {
      return [];
    }
    const rows: {key: string; def: string; type: PartitionRequestType}[] = [];
    requests.forEach(({partitionKeys, partitionsDefName, type}) => {
      partitionKeys?.forEach((key) => {
        rows.push({
          key,
          def: partitionsDefName,
          type,
        });
      });
    });
    return rows;
  }, [requests]);

  if (!rows.length) {
    return null;
  }

  return (
    <Box flex={{direction: 'column', gap: 12, grow: 1}} margin={{top: 24}}>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
        <Icon name="partition" />
        <Subheading>Dynamic Partition Requests</Subheading>
      </Box>
      <Table style={{borderRight: `1px solid ${Colors.KeylineGray}`}}>
        <thead>
          <tr>
            <th>Partition</th>
            <th>Partition definition</th>
            <th>Requested change</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({key, def, type}, index) => {
            return (
              <tr key={index}>
                <td>{key}</td>
                <td>{def}</td>
                <td>
                  {type === PartitionRequestType.ADD_PARTITIONS ? (
                    <Tag intent="success">
                      <span>Add Partition</span>
                    </Tag>
                  ) : (
                    <Tag intent="danger">
                      <span>Delete Partition</span>
                    </Tag>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </Box>
  );
}
