import {Box, Colors, Icon} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

export type ConditionType = 'group' | 'leaf';

interface Props {
  depth: number;
  icon: React.ReactNode;
  label: React.ReactNode;
  type: ConditionType;
  skipped?: boolean;
  isExpanded: boolean;
  hasChildren: boolean;
}

export const PolicyEvaluationCondition = (props: Props) => {
  const {depth, icon, label, type, skipped = false, isExpanded, hasChildren} = props;
  const depthLines = React.useMemo(() => {
    return new Array(depth).fill(null).map((_, ii) => <DepthLine key={ii} />);
  }, [depth]);

  return (
    <Box
      padding={{vertical: 2, horizontal: 8}}
      flex={{direction: 'row', alignItems: 'center', gap: 8}}
    >
      {depthLines}
      {hasChildren ? (
        <Icon
          name="arrow_drop_down"
          size={20}
          style={{transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)'}}
        />
      ) : null}
      {hasChildren ? icon : <div style={{marginLeft: 28}}>{icon}</div>}
      <ConditionLabel $type={type} $skipped={skipped}>
        {label}
      </ConditionLabel>
    </Box>
  );
};

const DepthLine = styled.div`
  background-color: ${Colors.keylineDefault()};
  align-self: stretch;
  margin: 0 4px 0 7px; /* 7px to align with center of icon in row above */
  width: 2px;
`;

interface ConditionLabelProps {
  $type: ConditionType;
  $skipped: boolean;
}

const ConditionLabel = styled.div<ConditionLabelProps>`
  font-weight: ${({$type}) => ($type === 'group' ? '600' : '400')};
  color: ${({$skipped}) => ($skipped ? Colors.textDisabled() : Colors.textDefault())};
`;
