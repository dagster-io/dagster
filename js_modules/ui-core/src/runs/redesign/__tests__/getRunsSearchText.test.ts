import {tokenizedValuesFromStringArray, tokensAsStringArray} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';

import {RunStatus} from '../../../graphql/types';
import {RunFilterToken, runsFilterForSearchTokens} from '../../RunsFilterUtils';
import {getRunsSearchText} from '../getRunsSearchText';
import {parseRunsSearch} from '../parseRunsSearch';

// The token types `useQueryPersistedRunFilters` decodes from `q[]`.
const URL_TOKEN_PROVIDERS = [
  'id',
  'status',
  'pipeline',
  'job',
  'tag',
  'snapshotId',
  'created_date_before',
  'created_date_after',
].map((token) => ({token, values: () => []}));

const decodeQuery = (query: string[]) =>
  tokenizedValuesFromStringArray(query, URL_TOKEN_PROVIDERS) as RunFilterToken[];

const getNormalizedFilter = (tokens: RunFilterToken[]) => {
  const {runIds, statuses, ...filter} = runsFilterForSearchTokens(tokens);
  return {
    ...filter,
    runIds: runIds ? [...new Set(runIds)].sort() : undefined,
    statuses: statuses ? [...new Set(statuses)].sort() : undefined,
  };
};

const parseTokens = (text: string) => {
  const {tokens, errors} = parseRunsSearch(text);
  if (!tokens) {
    throw new Error(`Expected "${text}" to parse: ${errors[0]?.message}`);
  }
  return tokens;
};

const LEGACY_QUERIES = [
  ['id:8d3e6c1a-4f2b-4c3d-9e8f-0a1b2c3d4e5f'],
  ['id:a', 'id:b', 'id:a'],
  ['status:FAILURE', 'status:CANCELED'],
  ['job:my_job'],
  ['pipeline:old_job'],
  ['job:first', 'pipeline:second'],
  ['snapshotId:abc', 'snapshotId:def'],
  ['created_date_after:1700000000.123'],
  ['created_date_before:1700000000', 'created_date_before:1700000500.5'],
  ['tag:dagster/partition=2024-01-01'],
  ['tag:.dagster/repository=repo@location'],
  ['tag:dagster/auto_materialize=true'],
  ['tag:team=data', 'tag:owner=ops'],
  ['tag:a=b=c'],
  ['tag:novalue'],
  ['tag:dagster/partition='],
  ['tag:pattern=a*b'],
  ['job:a*'],
  ['tag:.custom/key=x'],
  ['job:and'],
  ['some free text', 'foo:bar'],
  [
    'status:QUEUED',
    'job:etl',
    'tag:dagster/sensor_name=s',
    'id:abc-123',
    'created_date_after:1700000000',
  ],
];

describe('getRunsSearchText', () => {
  it.each([
    {query: [], text: ''},
    {query: ['id:a'], text: 'id:a'},
    {query: ['id:a', 'id:b', 'id:a'], text: '(id:a or id:b)'},
    {query: ['status:FAILURE', 'status:CANCELED'], text: '(status:FAILURE or status:CANCELED)'},
    {query: ['pipeline:old_job'], text: 'job:old_job'},
    {query: ['job:first', 'pipeline:second'], text: 'job:second'},
    {query: ['snapshotId:abc'], text: 'snapshot_id:abc'},
    {query: ['created_date_after:1700000000.5'], text: 'created_after:"1700000000.5"'},
    {query: ['id:abc-123'], text: 'id:"abc-123"'},
    {query: ['tag:.dagster/repository=repo@loc'], text: 'code_location:"repo@loc"'},
    {query: ['tag:dagster/auto_materialize=true'], text: 'tag:dagster/auto_materialize=true'},
    {query: ['tag:.custom/key=x'], text: 'tag:".custom/key"=x'},
    {query: ['tag:a=b=c'], text: 'tag:a=b'},
    {query: ['tag:novalue'], text: 'tag:novalue=""'},
    {query: ['tag:dagster/partition='], text: 'tag:dagster/partition=""'},
    {query: ['job:and'], text: 'job:"and"'},
    {query: ['some free text', 'foo:bar'], text: ''},
    {
      query: [
        'tag:team=data',
        'created_date_after:1',
        'job:etl',
        'tag:dagster/sensor_name=s',
        'id:a',
      ],
      text: 'id:a and job:etl and sensor:s and tag:team=data and created_after:1',
    },
  ])('renders $query as "$text"', ({query, text}) => {
    expect(getRunsSearchText(decodeQuery(query))).toBe(text);
  });

  it('drops partition and backfill tokens, which never filtered the query', () => {
    const tokens: RunFilterToken[] = [
      {token: 'partition', value: 'x'},
      {token: 'backfill', value: 'y'},
    ];
    expect(getRunsSearchText(tokens)).toBe('');
  });

  it.each(LEGACY_QUERIES.map((query) => ({query})))(
    'keeps the same server filter for $query after a render and parse',
    ({query}) => {
      const tokens = decodeQuery(query);
      const reparsed = parseTokens(getRunsSearchText(tokens));
      expect(getNormalizedFilter(reparsed)).toEqual(getNormalizedFilter(tokens));
    },
  );

  it.each([
    {text: 'tag:team=data and job:my_job and id:"abc-123" and sensor:s'},
    {text: 'tag:dagster/sensor_name=s and created_before:"1700000000.5"'},
    {text: 'user:"a@b.com" and code_location:"repo@loc" and partition:"2024-01-01"'},
  ])('treats the rendered form of $text as canonical', ({text}) => {
    const tokens = parseTokens(text);
    expect(tokensAsStringArray(parseTokens(getRunsSearchText(tokens)))).toEqual(
      tokensAsStringArray(tokens),
    );
  });

  it('renders tag values containing a quote even though the search cannot parse them', () => {
    const text = getRunsSearchText(decodeQuery(['tag:note=say "hi"']));
    expect(text).toBe('tag:note="say "hi""');
    expect(parseRunsSearch(text).tokens).toBeNull();
  });

  it('renders legacy conflicting tag values as-is for the editor to flag', () => {
    const text = getRunsSearchText(decodeQuery(['tag:team=a', 'tag:team=b']));
    expect(text).toBe('tag:team=a and tag:team=b');
    expect(parseRunsSearch(text).errors[0]?.message).toBe('Only one value per tag key');
  });
});

describe('render and parse across generated legacy tokens', () => {
  // Values that exercise quoting, keywords, operators, wildcards, whitespace, and `=`.
  const VALUES = [
    'a',
    'A1',
    '123',
    '1.5',
    'a-b',
    'a.b',
    'a@b',
    'a*b',
    '*',
    'a b',
    ' a',
    'a ',
    'a=b',
    'and',
    'OR',
    'not',
    'a/b',
    '/a',
    '_a',
    'a:b',
    'a,b',
    '(a)',
    'a+b',
    '+a',
    '<null>',
    'ä',
    '#6',
    'a\tb',
    "a'b",
  ];
  const TAG_KEYS = [
    'team',
    'dagster/partition',
    'dagster/sensor_name',
    '.dagster/repository',
    'user',
    ...VALUES,
  ];

  const getValidTokens = (): RunFilterToken[] => [
    ...['id', 'pipeline', 'job', 'snapshotId'].flatMap((token) =>
      VALUES.map((value) => ({token, value}) as RunFilterToken),
    ),
    ...Object.values(RunStatus).map((value) => ({token: 'status', value}) as RunFilterToken),
    ...['created_date_before', 'created_date_after'].flatMap((token) =>
      ['0', '1700000000', '1700000000.5'].map((value) => ({token, value}) as RunFilterToken),
    ),
    ...TAG_KEYS.flatMap((key) =>
      ['', ...VALUES].map((value) => ({token: 'tag', value: `${key}=${value}`}) as RunFilterToken),
    ),
  ];

  // Values the server can't filter on, plus characters that need grammar escapes.
  const getUnusableTokens = (): RunFilterToken[] => [
    ...['id', 'job', 'snapshotId', 'status', 'created_date_after'].map(
      (token) => ({token, value: ''}) as RunFilterToken,
    ),
    {token: 'status', value: 'bogus'},
    {token: 'created_date_before', value: 'soon'},
    {token: 'tag', value: '=a'},
    {token: 'tag', value: 'note=a"b'},
    {token: 'tag', value: 'note=a\\b'},
    {token: 'tag', value: 'note=a\nb'},
  ];

  const getRenderedFilter = (tokens: RunFilterToken[]) => {
    const reparsed = parseRunsSearch(getRunsSearchText(tokens)).tokens;
    return reparsed && getNormalizedFilter(reparsed);
  };

  it('keeps the server filter for every valid legacy token', () => {
    const changed = getValidTokens().filter(
      (token) => !isEqual(getRenderedFilter([token]), getNormalizedFilter([token])),
    );
    expect(changed).toEqual([]);
  });

  it('rejects unusable legacy tokens instead of changing the filter', () => {
    const accepted = getUnusableTokens().filter((token) => getRenderedFilter([token]) !== null);
    expect(accepted).toEqual([]);
  });
});
