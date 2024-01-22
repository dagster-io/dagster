import {Box, Colors, Icon, IconName} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

export type ConditionType = 'group' | 'leaf';

interface Props {
  depth: number;
  icon: IconName;
  label: React.ReactNode;
  type: ConditionType;
  skipped?: boolean;
}

export const PolicyEvaluationCondition = (props: Props) => {
  const {depth, icon, label, type, skipped = false} = props;
  const depthLines = React.useMemo(() => {
    return new Array(depth).fill(null).map((_, ii) => <DepthLine key={ii} />);
  }, [depth]);

  return (
    <Box
      padding={{vertical: 2, horizontal: 8}}
      flex={{direction: 'row', alignItems: 'center', gap: 8}}
      style={{height: '48px'}}
    >
      {depthLines}
      <Icon name={icon} color={Colors.accentPrimary()} />
      <ConditionLabel $type={type} $skipped={skipped}>
        {label}
      </ConditionLabel>
    </Box>
  );
};

const DepthLine = styled.div`
  background-color: ${Colors.keylineDefault()};
  height: 100%;
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
