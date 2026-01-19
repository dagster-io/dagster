import {
  Automation,
  automationSelectionSyntaxSupportedAttributes,
  useAutomationSelectionAutoCompleteProvider,
} from './useAutomationSelectionAutoCompleteProvider';
import {SelectionAutoCompleteInput} from '../../selection/SelectionInput';
import {createSelectionLinter} from '../../selection/createSelectionLinter';
import {weakMapMemoize} from '../../util/weakMapMemoize';
import {AutomationSelectionLexer} from '../generated/AutomationSelectionLexer';
import {AutomationSelectionParser} from '../generated/AutomationSelectionParser';

export const AutomationSelectionInput = ({
  items,
  value,
  onChange,
}: {
  items: Automation[];
  value: string;
  onChange: (value: string) => void;
}) => {
  return (
    <SelectionAutoCompleteInput
      wildcardAttributeName="name"
      id="automation-selection"
      useAutoComplete={useAutomationSelectionAutoCompleteProvider(items).useAutoComplete}
      placeholder="搜索和筛选自动化"
      linter={getLinter()}
      value={value}
      onChange={onChange}
    />
  );
};

const getLinter = weakMapMemoize(() =>
  createSelectionLinter({
    Lexer: AutomationSelectionLexer,
    Parser: AutomationSelectionParser,
    supportedAttributes: automationSelectionSyntaxSupportedAttributes,
  }),
);
