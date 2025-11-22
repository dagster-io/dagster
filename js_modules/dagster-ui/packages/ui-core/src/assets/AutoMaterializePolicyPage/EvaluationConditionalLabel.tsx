import {
  Box,
  CaptionMono,
  Code,
  Colors,
  FontFamily,
  Icon,
  MiddleTruncate,
  Tooltip,
} from '@dagster-io/ui-components';
import {useContext} from 'react';
import styled from 'styled-components';

import {EvaluationHistoryStackItem} from './types';
import {NewEvaluationNodeFragment} from './types/GetEvaluationsQuery.types';
import {TimeContext} from '../../app/time/TimeContext';
import {DEFAULT_TIME_FORMAT} from '../../app/time/TimestampFormat';
import {timestampToString} from '../../app/time/timestampToString';

interface Props {
  segments: string[];
}

export const EvaluationSinceLabel = ({
  evaluation,
  pushHistory,
}: {
  evaluation: NewEvaluationNodeFragment;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  const {
    timezone: [userTimezone],
    hourCycle: [userHourCycle],
  } = useContext(TimeContext);

  const locale = navigator.language;
  const {expandedLabel, sinceMetadata, entityKey} = evaluation;

  if (!sinceMetadata || expandedLabel.length !== 3 || expandedLabel[1] !== 'SINCE') {
    throw new Error(
      'sinceMetadata must be set and expandedLabel must be of the form [condition, SINCE, condition]',
    );
  }

  if (!sinceMetadata.triggerTimestamp || !sinceMetadata.resetTimestamp) {
    throw new Error('sinceMetadata must have both triggerTimestamp and resetTimestamp set');
  }

  const [triggerCondition, _operator, resetCondition] = expandedLabel;
  const triggerLabel = triggerCondition?.slice(1, -1) || ''; // remove parentheses
  const resetLabel = resetCondition?.slice(1, -1) || ''; // remove parentheses
  const triggerTime = timestampToString({
    timestamp: {unix: sinceMetadata.triggerTimestamp},
    locale,
    timezone: userTimezone,
    timeFormat: DEFAULT_TIME_FORMAT,
    hourCycle: userHourCycle,
  });
  const resetTime = timestampToString({
    timestamp: {unix: sinceMetadata.resetTimestamp},
    locale,
    timezone: userTimezone,
    timeFormat: DEFAULT_TIME_FORMAT,
    hourCycle: userHourCycle,
  });

  const assetKey =
    entityKey && entityKey.__typename === 'AssetCheckhandle' ? entityKey.assetKey : entityKey;
  const checkName =
    entityKey && entityKey.__typename === 'AssetCheckhandle' ? entityKey.name : undefined;

  return (
    <Box flex={{direction: 'row', gap: 8, wrap: 'wrap', alignItems: 'center'}}>
      <Tooltip content={<TooltipContent text={triggerLabel} />} placement="top">
        <Operand>{triggerLabel}</Operand>
      </Tooltip>
      <EvaluationSinceMetadata
        assetKey={assetKey}
        checkName={checkName}
        detailLabel={`${triggerLabel} was last True at ${triggerTime}`}
        evaluationId={sinceMetadata.triggerEvaluationId || 0}
        timestamp={sinceMetadata.triggerTimestamp || 0}
        pushHistory={pushHistory}
      />
      <Operator>SINCE</Operator>
      <Tooltip content={<TooltipContent text={resetLabel} />} placement="top">
        <Operand>{resetLabel}</Operand>
      </Tooltip>
      <EvaluationSinceMetadata
        assetKey={assetKey}
        checkName={checkName}
        detailLabel={`${resetLabel} last occurred ${resetTime}`}
        evaluationId={sinceMetadata.resetEvaluationId || 0}
        timestamp={sinceMetadata.resetTimestamp || 0}
        pushHistory={pushHistory}
      />
    </Box>
  );
};

export const EvaluationSinceMetadata = ({
  assetKey,
  checkName,
  detailLabel,
  evaluationId,
  pushHistory,
}: {
  assetKey: {path: string[]};
  checkName?: string;
  detailLabel: string;
  evaluationId: number;
  timestamp: number;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  if (!pushHistory) {
    return (
      <Tooltip content={detailLabel}>
        <Icon name="info" color={Colors.accentGray()} style={{verticalAlign: 'middle'}} />
      </Tooltip>
    );
  }
  return (
    <Tooltip content={detailLabel}>
      <a
        onClick={(e) => {
          e?.stopPropagation();
          pushHistory({
            assetKeyPath: assetKey.path,
            assetCheckName: checkName,
            evaluationID: String(evaluationId),
          });
        }}
      >
        <Icon name="link" color={Colors.accentGray()} style={{verticalAlign: 'middle'}} />
      </a>
    </Tooltip>
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
              <Operand>{inner}</Operand>
            </Tooltip>
          );
        }
        return <Operator key={key}>{segment}</Operator>;
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
        <Operand small={small}>{displayLabel}</Operand>
      </Tooltip>
    </Box>
  );
};

const TooltipContent = ({text}: {text: string}) => {
  return (
    <div style={{maxWidth: '500px', whiteSpace: 'normal'}}>
      <CaptionMono>{text}</CaptionMono>
    </div>
  );
};

const Operand = styled(Code)<{small?: boolean}>`
  background-color: ${Colors.backgroundGray()};
  border-radius: 8px;
  color: ${Colors.textLight()};
  display: block;
  font-size: 12px;
  font-weight: 400;
  padding: ${({small}) => (small ? '1' : '4')}px 8px;
  max-width: 300px;
  outline: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const Operator = styled.div`
  font-size: 12px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.textDefault()};
`;
