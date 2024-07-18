import {Box, CaptionMono, Code, Colors, FontFamily, Tooltip} from '@dagster-io/ui-components';
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
            <Tooltip
              key={key}
              content={
                <div style={{maxWidth: '500px', whiteSpace: 'normal'}}>
                  <CaptionMono>{inner}</CaptionMono>
                </div>
              }
              placement="top"
            >
              <Operand>{inner}</Operand>
            </Tooltip>
          );
        }
        return <Operator key={key}>{segment}</Operator>;
      })}
    </Box>
  );
};

const Operand = styled(Code)`
  background-color: ${Colors.backgroundGray()};
  border-radius: 8px;
  color: ${Colors.textLight()};
  display: block;
  font-size: 12px;
  padding: 4px 8px;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const Operator = styled.div`
  font-size: 12px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.textDefault()};
`;
