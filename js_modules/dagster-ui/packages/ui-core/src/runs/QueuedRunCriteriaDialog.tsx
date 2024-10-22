import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogFooter,
  Icon,
  NonIdealState,
  SpinnerWithText,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import isPlainObject from 'lodash/isPlainObject';
import * as React from 'react';
import {Link} from 'react-router-dom';
import * as yaml from 'yaml';

import {QUEUED_RUN_CRITERIA_QUERY} from './QueuedRunCriteriaQuery';
import {useQuery} from '../apollo-client';
import {
  QueuedRunCriteriaQuery,
  QueuedRunCriteriaQueryVariables,
} from './types/QueuedRunCriteriaQuery.types';
import {RunFragment} from './types/RunFragments.types';
import {useRunQueueConfig} from '../instance/useRunQueueConfig';
import {StructuredContentTable} from '../metadata/MetadataEntry';
import {numberFormatter} from '../ui/formatters';

type TagConcurrencyLimit = {
  key: string;
  value?: string;
  limit: number;
};

interface DialogProps extends ContentProps {
  isOpen: boolean;
  onClose: () => void;
}

export const QueuedRunCriteriaDialog = (props: DialogProps) => {
  const {isOpen, onClose, run} = props;
  return (
    <Dialog
      isOpen={isOpen}
      title="Run queue criteria"
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
      style={{width: 700}}
    >
      <QueuedRunCriteriaDialogContent run={run} />
      <DialogFooter topBorder>
        <Button intent="primary" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

interface ContentProps {
  run: Pick<RunFragment, 'id' | 'tags'>;
}

const QueuedRunCriteriaDialogContent = ({run}: ContentProps) => {
  const runQueueConfig = useRunQueueConfig();

  const {data, loading} = useQuery<QueuedRunCriteriaQuery, QueuedRunCriteriaQueryVariables>(
    QUEUED_RUN_CRITERIA_QUERY,
    {
      variables: {
        runId: run.id,
      },
    },
  );

  const runTagMap = Object.fromEntries(run.tags.map(({key, value}) => [key, value]));
  const maxConcurrentRuns = runQueueConfig?.maxConcurrentRuns;
  const runTagLimits = React.useMemo(() => {
    try {
      if (!runQueueConfig?.tagConcurrencyLimitsYaml) {
        return undefined;
      }
      const limits: TagConcurrencyLimit[] = yaml.parse(runQueueConfig.tagConcurrencyLimitsYaml);
      return limits.filter(
        (limit) =>
          limit.key in runTagMap &&
          (limit.value === undefined ||
            limit.value === runTagMap[limit.key] ||
            // can be {"applyLimitPerUniqueValue": bool}
            isPlainObject(limit.value)),
      );
    } catch {
      return undefined;
    }
  }, [runQueueConfig, runTagMap]);

  if (!runQueueConfig || loading) {
    return (
      <Box padding={32} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading run queue criteria…" />
      </Box>
    );
  }

  if (!data || data.runOrError.__typename !== 'Run') {
    return (
      <Box padding={32} flex={{direction: 'row', justifyContent: 'center'}}>
        <NonIdealState
          icon="run"
          title="Queue criteria not found"
          description="Could not load queue criteria for this run."
        />
      </Box>
    );
  }

  const {rootConcurrencyKeys, hasUnconstrainedRootNodes} = data.runOrError;

  const priority = runTagMap['dagster/priority'];
  const runIsOpConcurrencyLimited =
    runQueueConfig?.isOpConcurrencyAware &&
    rootConcurrencyKeys &&
    rootConcurrencyKeys.length > 0 &&
    !hasUnconstrainedRootNodes;

  return (
    <Table>
      <tbody>
        {priority ? (
          <tr>
            <td>Priority</td>
            <td>{priority}</td>
          </tr>
        ) : null}
        {maxConcurrentRuns !== undefined ? (
          <tr>
            <td>Max concurrent runs</td>
            <td>{numberFormatter.format(maxConcurrentRuns)}</td>
          </tr>
        ) : null}
        {runTagLimits?.length ? (
          <tr>
            <td>Tag concurrency limits:</td>
            <td>
              {runTagLimits.map((limit, i) => (
                <div style={{overflow: 'auto', paddingBottom: 10}} key={`tagLimit:${i}`}>
                  <StructuredContentTable cellPadding="0" cellSpacing="0">
                    <tbody>
                      <tr>
                        <td style={{width: 80, fontSize: 12}}>
                          {limit.value !== undefined ? 'Tag' : 'Tag key'}
                        </td>
                        <td>
                          <Tag interactive>
                            {limit.value !== undefined
                              ? `${limit.key}=${JSON.stringify(limit.value)}` // might be obj so stringify
                              : limit.key}
                          </Tag>
                        </td>
                      </tr>
                      <tr>
                        <td style={{width: 80, fontSize: 12}}>Limit</td>
                        <td>{limit.limit}</td>
                      </tr>
                    </tbody>
                  </StructuredContentTable>
                </div>
              ))}
            </td>
          </tr>
        ) : null}
        {runIsOpConcurrencyLimited ? (
          <tr>
            <td>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div>Initial concurrency keys</div>
                <Tooltip
                  placement="bottom"
                  content="Op/asset concurrency limits are set on all of the initial steps in this run. This run will not start until there are available slots for at least one step."
                >
                  <Icon name="info" color={Colors.accentGray()} />
                </Tooltip>
              </Box>
            </td>
            <td>
              {rootConcurrencyKeys!.map((key, i) =>
                runQueueConfig ? (
                  <Tag interactive key={`rootConcurrency:${i}`}>
                    <Link to={`/concurrency?key=${key}`}>{key}</Link>
                  </Tag>
                ) : (
                  <Tag interactive key={`rootConcurrency:${i}`}>
                    {key}
                  </Tag>
                ),
              )}
            </td>
          </tr>
        ) : null}
      </tbody>
    </Table>
  );
};
