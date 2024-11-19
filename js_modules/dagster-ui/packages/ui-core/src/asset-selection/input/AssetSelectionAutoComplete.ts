import CodeMirror, {HintFunction, Hints} from 'codemirror';

import {assertUnreachable} from '../../app/Util';
import {AssetGraphQueryItem} from '../../asset-graph/useAssetGraphData';
import {buildRepoPathForHuman} from '../../workspace/buildRepoAddress';

export const possibleKeywords = [
  'key:',
  'key_substring:',
  'tag:',
  'owner:',
  'group:',
  'kind:',
  'code_location:',
  'sinks()',
  'roots()',
  'not',
  '*',
  '+',
];

const logicalOperators = ['and', 'or', '*', '+'];

export const createAssetSelectionHint = (assets: AssetGraphQueryItem[]): HintFunction => {
  const assetNamesSet: Set<string> = new Set();
  const tagNamesSet: Set<string> = new Set();
  const ownersSet: Set<string> = new Set();
  const groupsSet: Set<string> = new Set();
  const kindsSet: Set<string> = new Set();
  const codeLocationSet: Set<string> = new Set();

  assets.forEach((asset) => {
    assetNamesSet.add(asset.name);
    asset.node.tags.forEach((tag) => {
      if (tag.key && tag.value) {
        tagNamesSet.add(`${tag.key}=${tag.value}`);
      } else {
        tagNamesSet.add(tag.key);
      }
    });
    asset.node.owners.forEach((owner) => {
      switch (owner.__typename) {
        case 'TeamAssetOwner':
          ownersSet.add(owner.team);
          break;
        case 'UserAssetOwner':
          ownersSet.add(owner.email);
          break;
        default:
          assertUnreachable(owner);
      }
    });
    if (asset.node.groupName) {
      groupsSet.add(asset.node.groupName);
    }
    asset.node.kinds.forEach((kind) => {
      kindsSet.add(kind);
    });
    const location = buildRepoPathForHuman(
      asset.node.repository.name,
      asset.node.repository.location.name,
    );
    codeLocationSet.add(location);
  });

  const assetNames = Array.from(assetNamesSet).map(addQuotesToString);
  const tagNames = Array.from(tagNamesSet).map(addQuotesToString);
  const owners = Array.from(ownersSet).map(addQuotesToString);
  const groups = Array.from(groupsSet).map(addQuotesToString);
  const kinds = Array.from(kindsSet).map(addQuotesToString);
  const codeLocations = Array.from(codeLocationSet).map(addQuotesToString);

  return (cm: CodeMirror.Editor): Hints | undefined => {
    const cursor = cm.getCursor();
    const token = cm.getTokenAt(cursor);

    const indexOfToken: number = token.state.tokenIndex - 1;
    const allTokens = token.state.tokens;

    const previous2Tokens =
      token.string.trim() === ''
        ? [allTokens[indexOfToken - 1]?.text, allTokens[indexOfToken]?.text]
        : [allTokens[indexOfToken - 2]?.text, allTokens[indexOfToken - 1]?.text];

    let start = token.start;
    const end = token.end;
    const tokenString = token.string.trim();
    const tokenUpToCursor = cm.getRange(CodeMirror.Pos(cursor.line, start), cursor).trim();
    const unquotedTokenString = removeQuotesFromString(tokenString);

    const isAfterAttributeValue = previous2Tokens[0] === ':' && previous2Tokens[1] !== undefined;

    const isAfterParenthesizedExpressions =
      // if tokenUpToCursor === '' and tokenString ===') then the cursor is to the left of the parenthesis
      previous2Tokens[1] === ')' || (tokenString === ')' && tokenUpToCursor !== '');

    const isInKeyValue =
      (previous2Tokens[1] === ':' && token.string.trim() !== '') || tokenString === ':';

    const isTraversal = /^[*+]+$/.test(tokenString);

    const tokensBefore = allTokens
      .slice(0, indexOfToken + 1)
      .map((token: any) => token.text?.trim());
    const preTraversal = isTraversal && isPreTraversal(tokensBefore);
    const isPostTraversal = isTraversal && !preTraversal;

    const isEndOfKeyValueExpression =
      isInKeyValue &&
      tokenString.endsWith('"') &&
      tokenString.length > 2 &&
      tokenUpToCursor.endsWith('"');

    const isAfterTraversal = ['+', '*'].includes(previous2Tokens[1]);

    function getSuggestions() {
      if (isEndOfKeyValueExpression) {
        start = end;
      }

      if (
        isPostTraversal ||
        isAfterAttributeValue ||
        isAfterParenthesizedExpressions ||
        isEndOfKeyValueExpression ||
        isAfterTraversal
      ) {
        return logicalOperators;
      }

      if (isInKeyValue) {
        let type = previous2Tokens[0];
        if (tokenString === ':') {
          type = previous2Tokens[1];
        }
        switch (type) {
          case 'key_substring':
          case 'key':
            return assetNames;
          case 'tag':
            return tagNames;
          case 'owner':
            return owners;
          case 'group':
            return groups;
          case 'kind':
            return kinds;
          case 'code_location':
            return codeLocations;
        }
      }

      if (tokenString === '' || tokenString === '(' || tokenString === ')' || preTraversal) {
        return possibleKeywords;
      }
      return [
        `key_substring:"${unquotedTokenString}"`,
        `key:"${unquotedTokenString}"`,
        ...possibleKeywords,
      ];
    }

    let suggestions = getSuggestions();

    if (!(isTraversal || isEndOfKeyValueExpression || ['', ':', '(', ')'].includes(tokenString))) {
      suggestions = suggestions.filter(
        (item) =>
          item.startsWith(tokenString) ||
          item.startsWith(unquotedTokenString) ||
          item.includes(`:"${unquotedTokenString}`) ||
          item.startsWith(`"${unquotedTokenString}`),
      );
    }

    const list = suggestions.map((item) => {
      let text = item;
      if (token.string[0] === ' ') {
        text = ' ' + item;
      }
      if (tokenString === ':') {
        text = `:${item}`;
      }

      if (tokenString === '(') {
        text = `(${text}`;
      }
      if (tokenString === ')') {
        if (isAfterParenthesizedExpressions) {
          text = `) ${text}`;
        } else {
          text = `${text})`;
        }
      }

      const trimmedText = text.trim();

      if (isTraversal) {
        if (text === '+' || text === '*') {
          text = `${tokenString}${text}`;
        } else if (trimmedText === 'and' || trimmedText === 'or' || trimmedText === 'not') {
          text = `${tokenString} ${text}`;
        }
      } else if (trimmedText === 'and' || trimmedText === 'or' || trimmedText === 'not') {
        text = ` ${trimmedText} `; // Insert spaces around the logical operator
      }

      return {
        text: text.replaceAll(/(\s)+/g, ' ').replaceAll(/(")+/g, '"'),
        displayText: removeQuotesFromString(item),
      };
    });

    return {
      list,
      from: CodeMirror.Pos(cursor.line, start),
      to: CodeMirror.Pos(cursor.line, end),
    };
  };
};

const removeQuotesFromString = (value: string) => {
  if (value.length > 1 && value[0] === '"' && value[value.length - 1] === '"') {
    return value.slice(1, value.length - 1);
  }
  return value;
};

const addQuotesToString = (value: string) => `"${value}"`;

const isPreTraversal = (tokensBefore: string[]) => {
  // If there are no tokens before, it's the start of the line
  if (tokensBefore.length === 0) {
    return true;
  }

  const previousToken = tokensBefore[tokensBefore.length - 1];

  // Check if the previous token is 'and', 'or', or '('
  return (
    previousToken === 'and' ||
    previousToken === 'or' ||
    previousToken === '(' ||
    !previousToken ||
    tokensBefore.every((token) => ['*', '+'].includes(token))
  );
};
