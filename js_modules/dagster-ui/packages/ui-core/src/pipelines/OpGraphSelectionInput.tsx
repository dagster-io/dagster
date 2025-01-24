import {useMemo} from 'react';
import styled from 'styled-components';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {OpSelectionLexer} from '../op-selection/generated/OpSelectionLexer';
import {OpSelectionParser} from '../op-selection/generated/OpSelectionParser';
import {InputDiv, SelectionAutoCompleteInput} from '../selection/SelectionInput';
import {createSelectionLinter} from '../selection/createSelectionLinter';
import {useSelectionInputAutoComplete} from '../selection/useSelectionInputAutoComplete';
import {weakMapMemoize} from '../util/weakMapMemoize';

export const OpGraphSelectionInput = ({
  items,
  value,
  onChange,
}: {
  items: GraphQueryItem[];
  value: string;
  onChange: (value: string) => void;
}) => {
  const useAutoComplete = useMemo(() => createAutoComplete(items), [items]);
  return (
    <Wrapper>
      <SelectionAutoCompleteInput
        id="op-graph"
        useAutoComplete={useAutoComplete}
        placeholder="Search and filter ops"
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </Wrapper>
  );
};

function createAutoComplete(items: GraphQueryItem[]) {
  return function useAutoComplete(value: string, cursor: number) {
    const attributesMap = useMemo(() => {
      const names = new Set<string>();
      items.forEach((item) => {
        names.add(item.name);
      });
      return {name: Array.from(names)};
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
  createSelectionLinter({Lexer: OpSelectionLexer, Parser: OpSelectionParser}),
);

const FUNCTIONS = ['sinks', 'roots'];

const Wrapper = styled.div`
  ${InputDiv} {
    width: 24vw;
  }
`;
