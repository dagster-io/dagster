import {
  Box,
  ButtonLink,
  Code,
  Colors,
  Icon,
  MiddleTruncate,
  Tag,
  Text,
  Tooltip,
} from '@dagster-io/ui-components';
import clsx from 'clsx';

import styles from './css/EvaluationConditionalLabel.module.css';
import {
  EvaluationMemoryRow,
  assetCheckNameForEntityKey,
  assetKeyForEntityKey,
  jobNameForEntityKey,
} from './flattenEvaluations';
import {EvaluationHistoryStackItem} from './types';
import {useFormatDateTime} from '../../ui/useFormatDateTime';

interface Props {
  segments: string[];
}

/**
 * The tag on a memory row, naming the tick whose remembered value the row's status describes:
 * "current tick" / "last tick" for a newly_true edge, "set at <ts>" / "reset: never" (etc.) for a
 * since latch. Latch tags with a recorded tick navigate to that tick's evaluation, where the full
 * tree shows accurate historical values.
 */
export const TemporalTag = ({
  row,
  pushHistory,
}: {
  row: EvaluationMemoryRow;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  const formatDateTime = useFormatDateTime();
  const {tag, conditionLabel, entityKey} = row;

  if (tag.kind === 'currentTick') {
    return (
      <Tooltip content={`The value of ${conditionLabel} on this tick.`} placement="top">
        <Tag icon="preview_tick">current tick</Tag>
      </Tooltip>
    );
  }
  if (tag.kind === 'lastTick') {
    if (row.result.isPartitioned) {
      // The derived partitioned count is |true now ∩ true last tick|, not the full previous-tick
      // value — partitions that were true last tick but are no longer true are unknowable from the
      // record. "already true" labels what the count actually is.
      return (
        <Tooltip
          content={`Of the partitions where ${conditionLabel} is true now, how many were already true on the previous tick. The parent condition is true only for the remainder, which are newly true.`}
          placement="top"
        >
          <Tag icon="history">already true</Tag>
        </Tooltip>
      );
    }
    return (
      <Tooltip
        content={`The value of ${conditionLabel} on the previous tick. The parent condition is true only where ${conditionLabel} is true now but was not true on the previous tick.`}
        placement="top"
      >
        <Tag icon="history">last tick</Tag>
      </Tooltip>
    );
  }

  const verb = tag.kind;
  if (tag.timestamp === null) {
    return (
      <Tooltip content={`${conditionLabel} has not been True in tracked history.`} placement="top">
        <Tag icon="history_toggle_off">{`${verb}: never`}</Tag>
      </Tooltip>
    );
  }

  const time = formatDateTime(new Date(1000 * tag.timestamp), {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
  const detail = `${conditionLabel} was last True at ${time}${
    tag.evaluationId ? ` (evaluation ${tag.evaluationId})` : ''
  }`;
  const tagElement = <Tag icon="history">{`${verb} at ${time}`}</Tag>;

  if (!pushHistory || !tag.evaluationId) {
    return (
      <Tooltip content={detail} placement="top">
        {tagElement}
      </Tooltip>
    );
  }

  const assetKey = entityKey ? (assetKeyForEntityKey(entityKey) ?? undefined) : undefined;
  const checkName = entityKey ? assetCheckNameForEntityKey(entityKey) : undefined;
  const jobName = entityKey ? jobNameForEntityKey(entityKey) : undefined;
  const evaluationId = tag.evaluationId;
  return (
    <>
      {tagElement}
      <Tooltip
        content={`${conditionLabel} was last True at ${time}. Click to view evaluation ${evaluationId}.`}
        placement="top"
      >
        <ButtonLink
          onClick={(e) => {
            e?.stopPropagation();
            pushHistory({
              assetKeyPath: assetKey?.path,
              assetCheckName: checkName,
              jobName,
              evaluationID: evaluationId,
            });
          }}
        >
          <Icon name="link" color={Colors.accentGray()} style={{verticalAlign: 'middle'}} />
        </ButtonLink>
      </Tooltip>
    </>
  );
};

export const EvaluationMemoryRowLabel = ({
  row,
  pushHistory,
}: {
  row: EvaluationMemoryRow;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      <TemporalTag row={row} pushHistory={pushHistory} />
      <Tooltip content={<TooltipContent text={row.conditionLabel} />} placement="top">
        <Code className={styles.operand}>{row.conditionLabel}</Code>
      </Tooltip>
    </Box>
  );
};

export const EvaluationConditionalLabel = ({segments}: Props) => {
  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      {segments.map((segment, ii) => {
        const key = `segment-${ii}`;
        if (segment.startsWith('(') && segment.endsWith(')')) {
          const inner = segment.slice(1, -1);
          return (
            <Tooltip key={key} content={<TooltipContent text={inner} />} placement="top">
              <Code className={styles.operand}>{inner}</Code>
            </Tooltip>
          );
        }
        return (
          <div key={key} className={styles.operator}>
            {segment}
          </div>
        );
      })}
    </Box>
  );
};

interface EvaluationUserLabelProps {
  userLabel: string;
  expandedLabel: string[];
  small?: boolean;
}

export const EvaluationUserLabel = ({
  userLabel,
  expandedLabel,
  small,
}: EvaluationUserLabelProps) => {
  const displayLabel = small ? <MiddleTruncate text={userLabel} /> : userLabel;
  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      <Tooltip content={<TooltipContent text={expandedLabel.join(' ')} />} placement="top">
        <Code className={clsx(styles.operand, small && styles.operandSmall)}>{displayLabel}</Code>
      </Tooltip>
    </Box>
  );
};

const TooltipContent = ({text}: {text: string}) => {
  return (
    <div style={{maxWidth: '500px', whiteSpace: 'normal'}}>
      <Text size={12} family="mono">
        {text}
      </Text>
    </div>
  );
};
