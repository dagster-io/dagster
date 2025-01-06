import {useMemo} from 'react';
import styled from 'styled-components';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {OpSelectionLexer} from '../op-selection/generated/OpSelectionLexer';
import {OpSelectionParser} from '../op-selection/generated/OpSelectionParser';
import {InputDiv, SelectionAutoCompleteInput} from '../selection/SelectionAutoCompleteInput';
import {createSelectionLinter} from '../selection/createSelectionLinter';
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
  const attributesMap = useMemo(() => {
    const names = new Set<string>();
    items.forEach((item) => {
      names.add(item.name);
    });
    return {name: Array.from(names)};
  }, [items]);

  return (
    <Wrapper>
      <SelectionAutoCompleteInput
        id="op-graph"
        nameBase="name"
        attributesMap={attributesMap}
        placeholder="Type an op subset"
        functions={FUNCTIONS}
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </Wrapper>
  );
};

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({Lexer: OpSelectionLexer, Parser: OpSelectionParser}),
);

const FUNCTIONS = ['sinks', 'roots'];

const Wrapper = styled.div`
  ${InputDiv} {
    width: 24vw;
  }
`;
