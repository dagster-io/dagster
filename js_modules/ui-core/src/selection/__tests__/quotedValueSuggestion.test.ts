import {MockedProvider} from '@apollo/client/testing';
import {render, renderHook} from '@testing-library/react';
import {ReactNode, createElement} from 'react';

import {AssetSelectionLexer} from '../../asset-selection/generated/AssetSelectionLexer';
import {AssetSelectionParser} from '../../asset-selection/generated/AssetSelectionParser';
import {assetSelectionSyntaxSupportedAttributes} from '../../asset-selection/input/util';
import {AutomationSelectionLexer} from '../../automation-selection/generated/AutomationSelectionLexer';
import {AutomationSelectionParser} from '../../automation-selection/generated/AutomationSelectionParser';
import {automationSelectionSyntaxSupportedAttributes} from '../../automation-selection/input/useAutomationSelectionAutoCompleteProvider';
import {ganttChartSelectionSyntaxSupportedAttributes} from '../../gantt/useGanttChartSelectionAutoCompleteProvider';
import {JobSelectionLexer} from '../../job-selection/generated/JobSelectionLexer';
import {JobSelectionParser} from '../../job-selection/generated/JobSelectionParser';
import {jobSelectionSyntaxSupportedAttributes} from '../../job-selection/input/useJobSelectionAutoCompleteProvider';
import {OpSelectionLexer} from '../../op-selection/generated/OpSelectionLexer';
import {OpSelectionParser} from '../../op-selection/generated/OpSelectionParser';
import {opGraphSelectionSyntaxSupportedAttributes} from '../../pipelines/useOpGraphSelectionAutoCompleteProvider';
import {RunSelectionLexer} from '../../run-selection/generated/RunSelectionLexer';
import {RunSelectionParser} from '../../run-selection/generated/RunSelectionParser';
import {parseRunsSearch} from '../../runs/redesign/parseRunsSearch';
import {useRunsSearchAutoCompleteProvider} from '../../runs/redesign/useRunsSearchAutoCompleteProvider';
import {SyntaxError} from '../CustomErrorListener';
import {createSelectionAutoComplete} from '../SelectionAutoComplete';
import {createProvider} from '../SelectionAutoCompleteProvider';
import {createSelectionLinter} from '../createSelectionLinter';

type AutoCompleteResults = ReturnType<ReturnType<typeof createSelectionAutoComplete>>;

type Consumer = {
  name: string;
  getResults: (line: string, cursorIndex: number) => AutoCompleteResults;
  lint: (text: string) => SyntaxError[];
  /** Inputs whose quoted row the page should accept. */
  quoted: string[];
  /** Inputs where quoting can't fix the expression, so the row is held back. */
  heldBack: string[];
};

const createHint = (
  attributes: readonly string[],
  primaryAttributeKey: string,
  supportsTraversal: boolean,
) =>
  createSelectionAutoComplete({
    ...createProvider({
      attributesMap: Object.fromEntries(attributes.map((attribute) => [attribute, []])),
      attributeToIcon: Object.fromEntries(
        attributes.map((attribute) => [attribute, 'magnify_glass' as const]),
      ),
      primaryAttributeKey,
    }),
    supportsTraversal,
  });

type RunsSearchMocksProps = {
  children: ReactNode;
};

const RunsSearchMocks = ({children}: RunsSearchMocksProps) =>
  createElement(MockedProvider, {mocks: []}, children);

const getRunsSearchResults = (line: string, cursorIndex: number) =>
  renderHook(() => useRunsSearchAutoCompleteProvider().useAutoComplete({line, cursorIndex}), {
    wrapper: RunsSearchMocks,
  }).result.current.autoCompleteResults;

const CONSUMERS: Consumer[] = [
  {
    name: 'asset selection',
    getResults: createHint(assetSelectionSyntaxSupportedAttributes, 'key', true),
    lint: createSelectionLinter({
      Lexer: AssetSelectionLexer,
      Parser: AssetSelectionParser,
      supportedAttributes: assetSelectionSyntaxSupportedAttributes,
    }),
    quoted: [
      'owner:zzz@q',
      'owner:a-b',
      'group:a.b',
      'key:a-b*',
      'tag:a-b=c-d',
      'tag:a-b=<null>',
      'tag:a-b|="star*"',
    ],
    heldBack: ['owner:a-b*'],
  },
  {
    name: 'job selection',
    getResults: createHint(jobSelectionSyntaxSupportedAttributes, 'name', false),
    lint: createSelectionLinter({
      Lexer: JobSelectionLexer,
      Parser: JobSelectionParser,
      supportedAttributes: jobSelectionSyntaxSupportedAttributes,
    }),
    quoted: ['name:zzz@q', 'name:a-b', 'code_location:a.b', 'name:a-b*'],
    heldBack: ['name:a-b=c-d'],
  },
  {
    name: 'automation selection',
    getResults: createHint(automationSelectionSyntaxSupportedAttributes, 'name', false),
    lint: createSelectionLinter({
      Lexer: AutomationSelectionLexer,
      Parser: AutomationSelectionParser,
      supportedAttributes: automationSelectionSyntaxSupportedAttributes,
    }),
    quoted: [
      'name:zzz@q',
      'name:a-b',
      'code_location:a.b',
      'name:a-b*',
      'tag:a-b=c-d',
      'tag:a-b=<null>',
      'tag:a-b|="star*"',
    ],
    heldBack: ['name:a-b=c-d', 'tag:a-b=c*', 'tag:a*=c-d'],
  },
  {
    name: 'op graph selection',
    getResults: createHint(opGraphSelectionSyntaxSupportedAttributes, 'name', true),
    lint: createSelectionLinter({
      Lexer: OpSelectionLexer,
      Parser: OpSelectionParser,
      supportedAttributes: opGraphSelectionSyntaxSupportedAttributes,
    }),
    quoted: ['name:zzz@q', 'name:a-b', 'name:a.b', 'name:a-b*'],
    heldBack: ['name:a-b=c-d'],
  },
  {
    name: 'gantt chart selection',
    getResults: createHint(ganttChartSelectionSyntaxSupportedAttributes, 'name', true),
    lint: createSelectionLinter({
      Lexer: RunSelectionLexer,
      Parser: RunSelectionParser,
      supportedAttributes: ganttChartSelectionSyntaxSupportedAttributes,
    }),
    quoted: ['name:zzz@q', 'name:a-b', 'status:a.b', 'name:a-b*'],
    heldBack: ['name:a-b=c-d'],
  },
  {
    name: 'Runs search',
    getResults: getRunsSearchResults,
    lint: (text) => parseRunsSearch(text).errors,
    quoted: ['job:zzz@q', 'id:12ab-34cd', 'code_location:a.b', 'tag:a-b=c-d', 'tag:a-b|="star*"'],
    heldBack: ['job:a-b=c-d', 'job:a-b*', 'tag:a-b=c*', 'tag:a*=c-d'],
  },
];

/** Results with the cursor at the input's `|`, or at the end without one. */
const getResultsAtCursor = (input: string, getResults: Consumer['getResults']) => {
  const cursorIndex = input.includes('|') ? input.indexOf('|') : input.length;
  const line = input.replace('|', '');
  return {line, ...getResults(line, cursorIndex)};
};

/** The input with its single "Add quotes" row applied, or null when there's no such row. */
const applyQuotedRow = (input: string, getResults: Consumer['getResults']) => {
  const {line, list, from, to} = getResultsAtCursor(input, getResults);
  const [row] = list;
  if (list.length !== 1 || !row || 'type' in row) {
    return null;
  }
  const {container, unmount} = render(row.jsx);
  const isQuotedRow = container.textContent?.startsWith('Add quotes:');
  unmount();
  if (!isQuotedRow) {
    return null;
  }
  return `${line.slice(0, from)}${row.text}${line.slice(to)}`;
};

describe('quoted value suggestion', () => {
  it.each(CONSUMERS)(
    'quotes values into text the $name accepts',
    ({getResults, lint, quoted, heldBack}) => {
      const fixes = quoted.map((input) => ({input, fix: applyQuotedRow(input, getResults)}));
      expect(
        fixes.map(({input, fix}) => ({input, fix, errors: fix === null ? null : lint(fix)})),
      ).toEqual(fixes.map(({input}) => ({input, fix: expect.any(String), errors: []})));

      expect(
        heldBack.map((input) => ({input, list: getResultsAtCursor(input, getResults).list})),
      ).toEqual(
        heldBack.map((input) => ({input, list: [expect.objectContaining({type: 'no-match'})]})),
      );
    },
  );
});
