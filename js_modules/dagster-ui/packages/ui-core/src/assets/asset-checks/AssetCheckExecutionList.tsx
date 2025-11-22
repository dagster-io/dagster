import {
  Box,
  Colors,
  CursorHistoryControls,
  CursorPaginationProps,
  Icon,
  Popover,
  SpinnerWithText,
  Table,
} from '@dagster-io/ui-components';
import {Link} from 'react-router-dom';

import {MetadataCell} from './AssetCheckDetailDialog';
import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {AssetCheckDetailsQuery} from './types/AssetCheckDetailDialog.types';
import {Description} from '../../pipelines/Description';
import {linkToRunEvent} from '../../runs/RunUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';

type Execution = AssetCheckDetailsQuery['assetCheckExecutions'][0];

export const AssetCheckExecutionList = ({
  executions,
  paginationProps,
  hasPartitions = false,
}: {
  executions: Execution[];
  paginationProps: CursorPaginationProps;
  hasPartitions?: boolean;
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
              {hasPartitions && <th style={{width: '150px'}}>Partition</th>}
              <th>
                <Box flex={{gap: 4}}>
                  Description
                  <PopoverToDocs
                    href="https://docs.dagster.io/_apidocs/asset-checks#dagster.AssetCheckResult.description"
                    label="Learn how to add a description to asset checks"
                  />
                </Box>
              </th>
              <th style={{width: '100px'}}>
                <Box flex={{gap: 4}}>
                  Metadata
                  <PopoverToDocs
                    href="https://docs.dagster.io/concepts/assets/asset-checks/define-execute-asset-checks#adding-metadata"
                    label="Learn how to add metadata to asset checks"
                  />
                </Box>
              </th>
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
                  {hasPartitions && (
                    <td>
                      {execution.evaluation?.partition ? execution.evaluation.partition : ' - '}
                    </td>
                  )}
                  <td>
                    {execution.evaluation?.description ? (
                      <Description fontSize="14px" description={execution.evaluation.description} />
                    ) : (
                      ' - '
                    )}
                  </td>
                  <td style={{textAlign: 'right'}}>
                    <MetadataCell
                      metadataEntries={execution.evaluation?.metadataEntries}
                      type="dialog"
                    />
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

const PopoverToDocs = ({href, label}: {href: string; label: string}) => (
  <Popover
    position="top"
    interactionKind="hover"
    content={
      <a target="_blank" href={href} rel="noreferrer">
        <Box
          padding={8}
          flex={{direction: 'row', gap: 4, alignItems: 'center'}}
          style={{whiteSpace: 'nowrap'}}
        >
          {label}
          <Icon name="open_in_new" color={Colors.linkDefault()} />
        </Box>
      </a>
    }
    hoverOpenDelay={100}
  >
    <Icon name="info" color={Colors.accentGray()} />
  </Popover>
);
