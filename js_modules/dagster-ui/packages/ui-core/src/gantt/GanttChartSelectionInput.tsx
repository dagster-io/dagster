import {useMemo} from 'react';
import styled from 'styled-components';

import {RunGraphQueryItem} from './toGraphQueryItems';
import {NO_STATE} from '../run-selection/AntlrRunSelectionVisitor';
import {RunSelectionLexer} from '../run-selection/generated/RunSelectionLexer';
import {RunSelectionParser} from '../run-selection/generated/RunSelectionParser';
import {InputDiv, SelectionAutoCompleteInput} from '../selection/SelectionAutoCompleteInput';
import {createSelectionLinter} from '../selection/createSelectionLinter';
import {weakMapMemoize} from '../util/weakMapMemoize';

export const GanttChartSelectionInput = ({
  items,
  value,
  onChange,
}: {
  items: RunGraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
}) => {
  const attributesMap = useMemo(() => {
    const statuses = new Set<string>();
    const names = new Set<string>();

    items.forEach((item) => {
      if (item.metadata?.state) {
        statuses.add(item.metadata.state);
      } else {
        statuses.add(NO_STATE);
      }
      names.add(item.name);
    });
    return {name: Array.from(names), status: Array.from(statuses)};
  }, [items]);

  return (
    <Wrapper>
      <SelectionAutoCompleteInput
        id="run-gantt-chart"
        nameBase="name"
        attributesMap={attributesMap}
        placeholder="Type a step subset"
        functions={FUNCTIONS}
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </Wrapper>
  );
};

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({Lexer: RunSelectionLexer, Parser: RunSelectionParser}),
);

const FUNCTIONS = ['sinks', 'roots'];

const Wrapper = styled.div`
  ${InputDiv} {
    width: 24vw;
  }
`;
