import {
  Box,
  ButtonLink,
  CaptionMono,
  Code,
  Colors,
  FontFamily,
  Icon,
  MiddleTruncate,
  Tooltip,
} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {EvaluationHistoryStackItem} from './types';
import {SinceMetadataFragment} from './types/GetEvaluationsQuery.types';
import {EntityKey} from '../../graphql/types';
import {useFormatDateTime} from '../../ui/useFormatDateTime';

interface Props {
  segments: string[];
}

export const EvaluationSinceLabel = ({
  sinceMetadata,
  triggerCondition,
  resetCondition,
  entityKey,
  pushHistory,
}: {
  triggerCondition?: string;
  resetCondition?: string;
  sinceMetadata: SinceMetadataFragment;
  entityKey: EntityKey;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  const formatDateTime = useFormatDateTime();

  const triggerLabel = triggerCondition?.slice(1, -1) || ''; // remove parentheses
  const resetLabel = resetCondition?.slice(1, -1) || ''; // remove parentheses
  const triggerTime = sinceMetadata.triggerTimestamp
    ? formatDateTime(new Date(1000 * sinceMetadata.triggerTimestamp), {
        timeStyle: 'long',
      })
    : null;
  const resetTime = sinceMetadata.resetTimestamp
    ? formatDateTime(new Date(1000 * sinceMetadata.resetTimestamp), {
        timeStyle: 'long',
      })
    : null;

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
        detailLabel={
          triggerTime
            ? `${triggerLabel} was last True at ${triggerTime}`
            : `${triggerLabel} has not yet occurred.`
        }
        evaluationId={sinceMetadata.triggerEvaluationId}
        timestamp={sinceMetadata.triggerTimestamp}
        pushHistory={pushHistory}
      />
      <Operator>SINCE</Operator>
      <Tooltip content={<TooltipContent text={resetLabel} />} placement="top">
        <Operand>{resetLabel}</Operand>
      </Tooltip>
      <EvaluationSinceMetadata
        assetKey={assetKey}
        checkName={checkName}
        detailLabel={
          resetTime
            ? `${resetLabel} last occurred ${resetTime}`
            : `${resetLabel} has not yet occured.`
        }
        evaluationId={sinceMetadata.resetEvaluationId}
        timestamp={sinceMetadata.resetTimestamp}
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
  timestamp,
  pushHistory,
}: {
  assetKey: {path: string[]};
  checkName?: string;
  detailLabel: string;
  evaluationId: string | null;
  timestamp: number | null;
  pushHistory?: (item: EvaluationHistoryStackItem) => void;
}) => {
  if (!pushHistory || !evaluationId || !timestamp) {
    return (
      <Tooltip content={detailLabel}>
        <Icon name="info" color={Colors.accentGray()} style={{verticalAlign: 'middle'}} />
      </Tooltip>
    );
  }
  return (
    <Tooltip content={detailLabel}>
      <ButtonLink
        onClick={() => {
          pushHistory({
            assetKeyPath: assetKey.path,
            assetCheckName: checkName,
            evaluationID: evaluationId,
          });
        }}
      >
        <Icon name="link" color={Colors.accentGray()} style={{verticalAlign: 'middle'}} />
      </ButtonLink>
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
