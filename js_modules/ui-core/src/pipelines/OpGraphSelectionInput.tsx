import styles from './css/OpGraphSelectionInput.module.css';
import {
  opGraphSelectionSyntaxSupportedAttributes,
  useOpGraphSelectionAutoCompleteProvider,
} from './useOpGraphSelectionAutoCompleteProvider';
import {GraphQueryItem} from '../app/GraphQueryImpl';
import {OpSelectionLexer} from '../op-selection/generated/OpSelectionLexer';
import {OpSelectionParser} from '../op-selection/generated/OpSelectionParser';
import {SelectionAutoCompleteInput} from '../selection/SelectionInput';
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
  return (
    <div className={styles.wrapper}>
      <SelectionAutoCompleteInput
        wildcardAttributeName="name"
        id="op-graph"
        useAutoComplete={useOpGraphSelectionAutoCompleteProvider(items).useAutoComplete}
        placeholder="Search and filter ops"
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </div>
  );
};

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({
    Lexer: OpSelectionLexer,
    Parser: OpSelectionParser,
    supportedAttributes: opGraphSelectionSyntaxSupportedAttributes,
  }),
);
