import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  Mono,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import * as yaml from 'yaml';

import {RunTableRunFragment} from './types/RunTable.types';
import {useRunQueueConfig} from '../instance/useRunQueueConfig';
import {StructuredContentTable} from '../metadata/MetadataEntry';

type TagConcurrencyLimit = {
  key: string;
  value?: string;
  limit: number;
};

export const QueuedRunCriteriaDialog = ({
  isOpen,
  onClose,
  run,
}: {
  isOpen: boolean;
  onClose: () => void;
  run: RunTableRunFragment;
}) => {
  const runQueueConfig = useRunQueueConfig();
  const runTagMap = React.useMemo(() => {
    const tagMap: {[key: string]: string} = {};
    run.tags.forEach((tag) => {
      tagMap[tag.key] = tag.value;
    });
    return tagMap;
  }, [run.tags]);
  const maxConcurrentRuns = runQueueConfig?.maxConcurrentRuns;
  const runTagLimits = React.useMemo(() => {
    try {
      if (!runQueueConfig?.tagConcurrencyLimitsYaml) {
        return undefined;
      }
      const limits: [TagConcurrencyLimit] = yaml.parse(runQueueConfig.tagConcurrencyLimitsYaml);
      return limits.filter(
        (limit) =>
          limit.key in runTagMap &&
          (limit.value === undefined || limit.value === runTagMap[limit.key]),
      );
    } catch (err) {
      return undefined;
    }
  }, [runQueueConfig, runTagMap]);
  const priority = runTagMap['dagster/priority'];
  const runIsOpConcurrencyLimited =
    runQueueConfig?.isOpConcurrencyAware &&
    run.rootConcurrencyKeys &&
    run.rootConcurrencyKeys.length > 0 &&
    !run.hasUnconstrainedRootNodes;

  return (
    <Dialog
      isOpen={isOpen}
      title="Run queue criteria"
      canOutsideClickClose
      canEscapeKeyClose
      onClose={onClose}
    >
      <DialogBody>
        <Table style={{borderRight: `1px solid ${Colors.keylineDefault()}`}}>
          <tbody>
            {priority ? (
              <tr>
                <td>Priority</td>
                <td>
                  <Mono>{priority}</Mono>
                </td>
              </tr>
            ) : null}
            {maxConcurrentRuns !== undefined ? (
              <tr>
                <td>Max concurrent runs</td>
                <td>
                  <Mono>{maxConcurrentRuns}</Mono>
                </td>
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
                                  ? `${limit.key}=${limit.value}`
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
                  <Box flex={{direction: 'row', alignItems: 'center'}}>
                    <Box margin={{right: 4}}>Root concurrency keys</Box>
                    <Tooltip
                      placement="bottom"
                      content="Op/asset concurrency limits are set on all of the initial steps in this run. This run will not start until there are available slots for at least one step"
                    >
                      <Icon name="info" color={Colors.accentGray()} />
                    </Tooltip>
                  </Box>
                </td>
                <td>
                  {run.rootConcurrencyKeys!.map((key, i) =>
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
      </DialogBody>
      <DialogFooter topBorder>
        <Button intent="primary" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
