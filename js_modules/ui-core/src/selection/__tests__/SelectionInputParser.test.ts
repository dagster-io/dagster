import {Trees} from 'antlr4ng';

import {parseInput} from '../SelectionInputParser';
import {ValueContext} from '../generated/SelectionAutoCompleteParser';

describe('parseInput', () => {
  it.each(['ben@and', 'not-x', '-or'])(
    'reads %s as one value, keeping keywords inside it',
    (input) => {
      const {parseTrees} = parseInput(input);
      const values = parseTrees.flatMap(({tree}) =>
        Trees.descendants(tree)
          .filter((node) => node instanceof ValueContext)
          .map((node) => node.getText()),
      );
      expect(parseTrees).toHaveLength(1);
      expect(values).toEqual([input]);
    },
  );
});
