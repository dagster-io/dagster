import {Box, Button, Colors, Dialog, DialogFooter, Mono, Table} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';

import styles from './AssetCheckHistoricalEventsButton.module.css';
import {assetCheckExecutionStatusText, getExecutionStatusIcon} from './util';
import {Timestamp} from '../../app/time/Timestamp';
import {AssetCheckSeverity, RunStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {RunStatusWithStats} from '../../runs/RunStatusDots';
import {titleForRun} from '../../runs/RunUtils';

interface AssetCheckExecutionForDisplay {
  id: string;
  runId: string;
  status: string;
  timestamp: number;
  run: {
    id: string;
    status: RunStatus;
  } | null;
  evaluation: {
    partition: string | null;
    severity?: string | null;
  } | null;
}

interface AssetCheckHistoricalEventsButtonProps {
  executions: AssetCheckExecutionForDisplay[];
  partitionKey?: string;
  children?: React.ReactNode;
  disabled?: boolean;
}

export const AssetCheckHistoricalEventsButton = ({
  executions,
  partitionKey,
  children,
  disabled,
}: AssetCheckHistoricalEventsButtonProps) => {
  const [_open, setOpen] = useQueryPersistedState<boolean>({
    queryKey: 'showAllCheckEvents',
    decode: (qs) => typeof qs.showAllCheckEvents === 'string' && qs.showAllCheckEvents === 'true',
    encode: (b) => ({showAllCheckEvents: b ? 'true' : undefined}),
  });

  const title = partitionKey
    ? `Historical check executions for ${partitionKey}`
    : `Historical check executions`;

  const hasPartitions = executions.some((e) => e.evaluation?.partition);

  const open = _open && !disabled;

  return (
    <>
      <Button disabled={disabled} onClick={() => setOpen(true)}>
        {children || `View all historical executions (${executions.length})`}
      </Button>
      <Dialog
        isOpen={open}
        canEscapeKeyClose
        canOutsideClickClose
        onClose={() => setOpen(false)}
        style={{width: '80%', minWidth: '800px'}}
        title={title}
      >
        {open && (
          <Box padding={{bottom: 8}}>
            <Table>
              <thead>
                <tr>
                  {hasPartitions && <th style={{minWidth: 100}}>Partition</th>}
                  <th style={{minWidth: 150}}>Timestamp</th>
                  <th style={{minWidth: 120}}>Status</th>
                  <th style={{width: 100}}>Run</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((execution) => (
                  <tr key={execution.id} className={styles.hoverableRow}>
                    {hasPartitions && (
                      <td style={{whiteSpace: 'nowrap', paddingLeft: 8}}>
                        {execution.evaluation?.partition || (
                          <span style={{color: Colors.textLight()}}>None</span>
                        )}
                      </td>
                    )}
                    <td>
                      <Timestamp timestamp={{unix: execution.timestamp}} />
                    </td>
                    <td>
                      <Box flex={{gap: 8, alignItems: 'center'}}>
                        {getExecutionStatusIcon(
                          execution.status as any,
                          execution.evaluation?.severity as AssetCheckSeverity | null,
                        )}
                        {assetCheckExecutionStatusText(execution.status as any)}
                      </Box>
                    </td>
                    <td>
                      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
                        {execution.run && (
                          <RunStatusWithStats
                            runId={execution.run.id}
                            status={execution.run.status}
                          />
                        )}
                        <Link to={`/runs/${execution.runId}?timestamp=${execution.timestamp}`}>
                          <Mono>{titleForRun({id: execution.runId})}</Mono>
                        </Link>
                      </Box>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Box>
        )}
        <DialogFooter>
          <Button intent="primary" onClick={() => setOpen(false)}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};
