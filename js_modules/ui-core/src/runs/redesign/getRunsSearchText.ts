import {
  RUNS_SEARCH_ATTRIBUTES,
  RunsSearchAttribute,
  formatRunsSearchValue,
  getAttributeTermForTag,
} from './runsSearchAttributes';
import {RunFilterToken, RunFilterTokenType, splitTagFilterValue} from '../RunsFilterUtils';

type RenderedTerm = {
  attribute: RunsSearchAttribute;
  text: string;
};

const getValues = (tokens: RunFilterToken[], types: RunFilterTokenType[]) =>
  tokens.filter(({token}) => token && types.includes(token)).map(({value}) => value);

const getScalarTerms = (
  attribute: RunsSearchAttribute,
  value: string | undefined,
): RenderedTerm[] =>
  value !== undefined ? [{attribute, text: `${attribute}:${formatRunsSearchValue(value)}`}] : [];

const getTagTerm = (tagValue: string): RenderedTerm => {
  const {key, value} = splitTagFilterValue(tagValue);
  const attributeTerm = getAttributeTermForTag(key, value);

  if (attributeTerm) {
    return {
      attribute: attributeTerm.attribute,
      text: `${attributeTerm.attribute}:${formatRunsSearchValue(attributeTerm.value)}`,
    };
  }
  return {
    attribute: 'tag',
    text: `tag:${formatRunsSearchValue(key)}=${formatRunsSearchValue(value)}`,
  };
};

/**
 * Renders legacy `q[]` tokens as runs search text.
 *
 * - Follows `runsFilterForSearchTokens` precedence: the last job and snapshot win; IDs,
 *   statuses, and tags accumulate.
 * - Drops tokens that converter ignores, and created-date tokens, which have their own control.
 */
export const getRunsSearchText = (tokens: RunFilterToken[]) => {
  const terms: RenderedTerm[] = [
    ...getValues(tokens, ['id']).map((value) => ({
      attribute: 'id' as const,
      text: `id:${formatRunsSearchValue(value)}`,
    })),
    ...getValues(tokens, ['status']).map((value) => ({
      attribute: 'status' as const,
      text: `status:${formatRunsSearchValue(value)}`,
    })),
    ...getScalarTerms('job', getValues(tokens, ['job', 'pipeline']).at(-1)),
    ...getScalarTerms('snapshot_id', getValues(tokens, ['snapshotId']).at(-1)),
    ...getValues(tokens, ['tag']).map(getTagTerm),
  ];

  return RUNS_SEARCH_ATTRIBUTES.flatMap((attribute) => {
    // Legacy URLs can repeat a token, and different tag spellings can render the same term.
    const texts = [
      ...new Set(terms.filter((term) => term.attribute === attribute).map((term) => term.text)),
    ];
    if ((attribute === 'id' || attribute === 'status') && texts.length > 1) {
      return [`(${texts.join(' or ')})`];
    }
    return texts;
  }).join(' and ');
};
