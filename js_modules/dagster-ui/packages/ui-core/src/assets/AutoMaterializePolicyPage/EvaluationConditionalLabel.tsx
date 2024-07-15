import {Box, Code, Colors, FontFamily} from '@dagster-io/ui-components';
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
          return <Operand key={key}>{segment.slice(1, -1)}</Operand>;
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
  font-size: 12px;
  padding: 4px 8px;
`;

const Operator = styled.div`
  font-size: 12px;
  font-family: ${FontFamily.monospace};
  color: ${Colors.textDefault()};
`;
