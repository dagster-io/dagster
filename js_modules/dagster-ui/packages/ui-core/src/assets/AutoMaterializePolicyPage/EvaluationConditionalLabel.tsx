import {
  Box,
  CaptionMono,
  Code,
  Colors,
  FontFamily,
  MiddleTruncate,
  Tooltip,
} from '@dagster-io/ui-components';
import styled from 'styled-components';

interface Props {
  segments: string[];
}

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
