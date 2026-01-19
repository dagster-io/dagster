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
import * as yaml from 'yaml';

import {QUEUED_RUN_CRITERIA_QUERY} from './QueuedRunCriteriaQuery';
import {useQuery} from '../apollo-client';
import {
  QueuedRunCriteriaQuery,
  QueuedRunCriteriaQueryVariables,
} from './types/QueuedRunCriteriaQuery.types';
import {RunFragment} from './types/RunFragments.types';
import {PoolTag} from '../instance/PoolTag';
import {useRunQueueConfig} from '../instance/useRunQueueConfig';
import {StructuredContentTable} from '../metadata/MetadataEntry';
import {numberFormatter} from '../ui/formatters';

type TagConcurrencyLimit = {
  key: string;
  value?: string;
  limit: number;
};

interface DialogProps {
  run: Pick<RunFragment, 'id' | 'tags'> | undefined;
  isOpen: boolean;
  onClose: () => void;
}

export const QueuedRunCriteriaDialog = (props: DialogProps) => {
  const {isOpen, onClose, run} = props;
  return (
    <Dialog
      isOpen={isOpen}
      title="运行队列条件"
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
      style={{width: 700}}
    >
      {run ? <QueuedRunCriteriaDialogContent run={run} /> : undefined}
      <DialogFooter topBorder>
        <Button intent="primary" onClick={onClose}>
          关闭
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

  const granularity = data?.instance.poolConfig?.poolGranularity;
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
        <SpinnerWithText label="加载运行队列条件…" />
      </Box>
    );
  }

  if (!data || data.runOrError.__typename !== 'Run') {
    return (
      <Box padding={32} flex={{direction: 'row', justifyContent: 'center'}}>
        <NonIdealState
          icon="run"
          title="未找到队列条件"
          description="无法加载此运行的队列条件。"
        />
      </Box>
    );
  }

  const {rootConcurrencyKeys, hasUnconstrainedRootNodes, allPools} = data.runOrError;

  const priority = runTagMap['dagster/priority'];
  const poolOpGranularityRunLimited =
    runQueueConfig?.isOpConcurrencyAware &&
    (!granularity || granularity === 'op') &&
    rootConcurrencyKeys &&
    rootConcurrencyKeys.length > 0 &&
    !hasUnconstrainedRootNodes;

  const poolRunGranularityRunLimited =
    runQueueConfig?.isOpConcurrencyAware && allPools && allPools.length > 0;

  return (
    <Table>
      <tbody>
        {priority ? (
          <tr>
            <td>优先级</td>
            <td>{priority}</td>
          </tr>
        ) : null}
        {maxConcurrentRuns !== undefined ? (
          <tr>
            <td>最大并发运行数</td>
            <td>{numberFormatter.format(maxConcurrentRuns)}</td>
          </tr>
        ) : null}
        {runTagLimits?.length ? (
          <tr>
            <td>标签并发限制:</td>
            <td>
              {runTagLimits.map((limit, i) => (
                <div style={{overflow: 'auto', paddingBottom: 10}} key={`tagLimit:${i}`}>
                  <StructuredContentTable cellPadding="0" cellSpacing="0">
                    <tbody>
                      <tr>
                        <td style={{width: 80, fontSize: 12}}>
                          {limit.value !== undefined ? '标签' : '标签键'}
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
                        <td style={{width: 80, fontSize: 12}}>限制</td>
                        <td>{limit.limit}</td>
                      </tr>
                    </tbody>
                  </StructuredContentTable>
                </div>
              ))}
            </td>
          </tr>
        ) : null}
        {poolOpGranularityRunLimited || poolRunGranularityRunLimited ? (
          <tr>
            <td>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <div>池</div>
                <Tooltip
                  placement="bottom"
                  content={
                    <div style={{maxWidth: 300}}>
                      {poolOpGranularityRunLimited
                        ? '此运行的所有初始步骤都设置了池限制。在至少有一个步骤有可用槽位之前，此运行不会开始。'
                        : '此运行的操作设置了池限制。在所有池都有可用槽位之前，此运行不会开始。'}
                    </div>
                  }
                >
                  <Icon name="info" color={Colors.accentGray()} />
                </Tooltip>
              </Box>
            </td>
            <td>
              {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
              {(poolOpGranularityRunLimited ? rootConcurrencyKeys : allPools)!.map((pool) => (
                <PoolTag key={pool} pool={pool} />
              ))}
            </td>
          </tr>
        ) : null}
      </tbody>
    </Table>
  );
};
