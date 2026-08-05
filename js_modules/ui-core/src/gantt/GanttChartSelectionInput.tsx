import styles from './css/GanttChartSelectionInput.module.css';
import {RunGraphQueryItem} from './toGraphQueryItems';
import {
  ganttChartSelectionSyntaxSupportedAttributes,
  useGanttChartSelectionAutoCompleteProvider,
} from './useGanttChartSelectionAutoCompleteProvider';
import {RunSelectionLexer} from '../run-selection/generated/RunSelectionLexer';
import {RunSelectionParser} from '../run-selection/generated/RunSelectionParser';
import {SelectionAutoCompleteInput} from '../selection/SelectionInput';
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
  return (
    <div className={styles.wrapper}>
      <SelectionAutoCompleteInput
        wildcardAttributeName="name"
        id="run-gantt-chart"
        useAutoComplete={useGanttChartSelectionAutoCompleteProvider(items).useAutoComplete}
        placeholder="Search and filter steps"
        linter={getLinter()}
        value={value}
        onChange={onChange}
      />
    </div>
  );
};
const getLinter = weakMapMemoize(() =>
  createSelectionLinter({
    Lexer: RunSelectionLexer,
    Parser: RunSelectionParser,
    supportedAttributes: ganttChartSelectionSyntaxSupportedAttributes,
  }),
);
