import {
  Box,
  CursorHistoryControls,
  CursorPaginationProps,
  SpinnerWithText,
  Table,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {MetadataCell} from './AssetCheckDetailDialog';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {AssetCheckDetailsQuery} from './types/AssetCheckDetailDialog.types';
import {linkToRunEvent} from '../../runs/RunUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

type Execution = AssetCheckDetailsQuery['assetCheckExecutions'][0];

export const AssetCheckExecutionList = ({
  executions,
  paginationProps,
}: {
  executions: Execution[];
  paginationProps: CursorPaginationProps;
}) => {
  if (!executions) {
    return (
      <Box flex={{direction: 'column'}} padding={24}>
        <SpinnerWithText label="Loading execution history…" />
      </Box>
    );
  }

  return (
    <Box flex={{direction: 'column'}}>
      <div>
        <Table>
          <thead>
            <tr>
              <th style={{width: '160px'}}>Evaluation result</th>
              <th style={{width: '200px'}}>Timestamp</th>
              <th style={{width: '200px'}}>Target materialization</th>
              <th>Metadata</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((execution) => {
              return (
                <tr key={execution.id}>
                  <td>
                    <AssetCheckStatusTag execution={execution} />
                  </td>
                  <td>
                    {execution.evaluation?.timestamp ? (
                      <Link
                        to={linkToRunEvent(
                          {id: execution.runId},
                          {stepKey: execution.stepKey, timestamp: execution.timestamp},
                        )}
                      >
                        <TimestampDisplay timestamp={execution.evaluation.timestamp} />
                      </Link>
                    ) : (
                      <TimestampDisplay timestamp={execution.timestamp} />
                    )}
                  </td>
                  <td>
                    {execution.evaluation?.targetMaterialization ? (
                      <Link to={`/runs/${execution.evaluation.targetMaterialization.runId}`}>
                        <TimestampDisplay
                          timestamp={execution.evaluation.targetMaterialization.timestamp}
                        />
                      </Link>
                    ) : (
                      ' - '
                    )}
                  </td>
                  <td>
                    <MetadataCell metadataEntries={execution.evaluation?.metadataEntries} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
        <div style={{paddingBottom: '16px'}}>
          <CursorHistoryControls {...paginationProps} />
        </div>
      </div>
    </Box>
  );
};
