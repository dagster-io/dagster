import {
  jobSelectionSyntaxSupportedAttributes,
  useJobSelectionAutoCompleteProvider,
} from './useJobSelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {Job} from '../AntlrJobSelection';
import {JobSelectionLexer} from '../generated/JobSelectionLexer';
import {JobSelectionParser} from '../generated/JobSelectionParser';

export const JobSelectionInput = ({
  items,
  value,
  onChange,
}: {
  items: Job[];
  value: string;
  onChange: (value: string) => void;
}) => {
  return (
    <SelectionAutoCompleteInput
      wildcardAttributeName="name"
      id="job-selection"
      useAutoComplete={useJobSelectionAutoCompleteProvider(items).useAutoComplete}
      placeholder="搜索和筛选作业"
      linter={getLinter()}
      value={value}
      onChange={onChange}
    />
  );
};

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({
    Lexer: JobSelectionLexer,
    Parser: JobSelectionParser,
    supportedAttributes: jobSelectionSyntaxSupportedAttributes,
  }),
);
