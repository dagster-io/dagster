import {useMemo} from 'react';
import styled from 'styled-components';

import {RunGraphQueryItem} from './toGraphQueryItems';
import {NO_STATE} from '../run-selection/AntlrRunSelectionVisitor';
import {RunSelectionLexer} from '../run-selection/generated/RunSelectionLexer';
import {RunSelectionParser} from '../run-selection/generated/RunSelectionParser';
import {InputDiv, SelectionAutoCompleteInput} from '../selection/SelectionInput';
import {createSelectionLinter} from '../selection/createSelectionLinter';
import {useSelectionInputAutoComplete} from '../selection/useSelectionInputAutoComplete';
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
  const useAutoComplete = useMemo(() => createAutoComplete(items), [items]);
  return (
    <Wrapper>
      <SelectionAutoCompleteInput
        id="run-gantt-chart"
        useAutoComplete={useAutoComplete}
        placeholder="Search and filter steps"
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </Wrapper>
  );
};

function createAutoComplete(items: RunGraphQueryItem[]) {
  return function useAutoComplete(value: string, cursor: number) {
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
    }, []);

    return {
      autoCompleteResults: useSelectionInputAutoComplete({
        nameBase: 'name',
        attributesMap,
        functions: FUNCTIONS,
        value,
        cursor,
      }),
      loading: false,
    };
  };
}

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({Lexer: RunSelectionLexer, Parser: RunSelectionParser}),
);

const FUNCTIONS = ['sinks', 'roots'];

const Wrapper = styled.div`
  ${InputDiv} {
    width: 24vw;
  }
`;
