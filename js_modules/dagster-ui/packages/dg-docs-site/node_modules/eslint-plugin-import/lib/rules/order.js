'use strict';var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) {return typeof obj;} : function (obj) {return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;};var _slicedToArray = function () {function sliceIterator(arr, i) {var _arr = [];var _n = true;var _d = false;var _e = undefined;try {for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) {_arr.push(_s.value);if (i && _arr.length === i) break;}} catch (err) {_d = true;_e = err;} finally {try {if (!_n && _i["return"]) _i["return"]();} finally {if (_d) throw _e;}}return _arr;}return function (arr, i) {if (Array.isArray(arr)) {return arr;} else if (Symbol.iterator in Object(arr)) {return sliceIterator(arr, i);} else {throw new TypeError("Invalid attempt to destructure non-iterable instance");}};}();

var _minimatch = require('minimatch');var _minimatch2 = _interopRequireDefault(_minimatch);
var _arrayIncludes = require('array-includes');var _arrayIncludes2 = _interopRequireDefault(_arrayIncludes);
var _object = require('object.groupby');var _object2 = _interopRequireDefault(_object);
var _contextCompat = require('eslint-module-utils/contextCompat');
var _stringPrototype = require('string.prototype.trimend');var _stringPrototype2 = _interopRequireDefault(_stringPrototype);

var _importType = require('../core/importType');var _importType2 = _interopRequireDefault(_importType);
var _staticRequire = require('../core/staticRequire');var _staticRequire2 = _interopRequireDefault(_staticRequire);
var _docsUrl = require('../docsUrl');var _docsUrl2 = _interopRequireDefault(_docsUrl);function _interopRequireDefault(obj) {return obj && obj.__esModule ? obj : { 'default': obj };}

var categories = {
  named: 'named',
  'import': 'import',
  exports: 'exports' };


var defaultGroups = ['builtin', 'external', 'parent', 'sibling', 'index'];

// REPORTING AND FIXING

function reverse(array) {
  return array.map(function (v) {return Object.assign({}, v, { rank: -v.rank });}).reverse();
}

function getTokensOrCommentsAfter(sourceCode, node, count) {
  var currentNodeOrToken = node;
  var result = [];
  for (var i = 0; i < count; i++) {
    currentNodeOrToken = sourceCode.getTokenOrCommentAfter(currentNodeOrToken);
    if (currentNodeOrToken == null) {
      break;
    }
    result.push(currentNodeOrToken);
  }
  return result;
}

function getTokensOrCommentsBefore(sourceCode, node, count) {
  var currentNodeOrToken = node;
  var result = [];
  for (var i = 0; i < count; i++) {
    currentNodeOrToken = sourceCode.getTokenOrCommentBefore(currentNodeOrToken);
    if (currentNodeOrToken == null) {
      break;
    }
    result.push(currentNodeOrToken);
  }
  return result.reverse();
}

function takeTokensAfterWhile(sourceCode, node, condition) {
  var tokens = getTokensOrCommentsAfter(sourceCode, node, 100);
  var result = [];
  for (var i = 0; i < tokens.length; i++) {
    if (condition(tokens[i])) {
      result.push(tokens[i]);
    } else {
      break;
    }
  }
  return result;
}

function takeTokensBeforeWhile(sourceCode, node, condition) {
  var tokens = getTokensOrCommentsBefore(sourceCode, node, 100);
  var result = [];
  for (var i = tokens.length - 1; i >= 0; i--) {
    if (condition(tokens[i])) {
      result.push(tokens[i]);
    } else {
      break;
    }
  }
  return result.reverse();
}

function findOutOfOrder(imported) {
  if (imported.length === 0) {
    return [];
  }
  var maxSeenRankNode = imported[0];
  return imported.filter(function (importedModule) {
    var res = importedModule.rank < maxSeenRankNode.rank;
    if (maxSeenRankNode.rank < importedModule.rank) {
      maxSeenRankNode = importedModule;
    }
    return res;
  });
}

function findRootNode(node) {
  var parent = node;
  while (parent.parent != null && parent.parent.body == null) {
    parent = parent.parent;
  }
  return parent;
}

function commentOnSameLineAs(node) {
  return function (token) {return (token.type === 'Block' || token.type === 'Line') &&
    token.loc.start.line === token.loc.end.line &&
    token.loc.end.line === node.loc.end.line;};
}

function findEndOfLineWithComments(sourceCode, node) {
  var tokensToEndOfLine = takeTokensAfterWhile(sourceCode, node, commentOnSameLineAs(node));
  var endOfTokens = tokensToEndOfLine.length > 0 ?
  tokensToEndOfLine[tokensToEndOfLine.length - 1].range[1] :
  node.range[1];
  var result = endOfTokens;
  for (var i = endOfTokens; i < sourceCode.text.length; i++) {
    if (sourceCode.text[i] === '\n') {
      result = i + 1;
      break;
    }
    if (sourceCode.text[i] !== ' ' && sourceCode.text[i] !== '\t' && sourceCode.text[i] !== '\r') {
      break;
    }
    result = i + 1;
  }
  return result;
}

function findStartOfLineWithComments(sourceCode, node) {
  var tokensToEndOfLine = takeTokensBeforeWhile(sourceCode, node, commentOnSameLineAs(node));
  var startOfTokens = tokensToEndOfLine.length > 0 ? tokensToEndOfLine[0].range[0] : node.range[0];
  var result = startOfTokens;
  for (var i = startOfTokens - 1; i > 0; i--) {
    if (sourceCode.text[i] !== ' ' && sourceCode.text[i] !== '\t') {
      break;
    }
    result = i;
  }
  return result;
}

function findSpecifierStart(sourceCode, node) {
  var token = void 0;

  do {
    token = sourceCode.getTokenBefore(node);
  } while (token.value !== ',' && token.value !== '{');

  return token.range[1];
}

function findSpecifierEnd(sourceCode, node) {
  var token = void 0;

  do {
    token = sourceCode.getTokenAfter(node);
  } while (token.value !== ',' && token.value !== '}');

  return token.range[0];
}

function isRequireExpression(expr) {
  return expr != null &&
  expr.type === 'CallExpression' &&
  expr.callee != null &&
  expr.callee.name === 'require' &&
  expr.arguments != null &&
  expr.arguments.length === 1 &&
  expr.arguments[0].type === 'Literal';
}

function isSupportedRequireModule(node) {
  if (node.type !== 'VariableDeclaration') {
    return false;
  }
  if (node.declarations.length !== 1) {
    return false;
  }
  var decl = node.declarations[0];
  var isPlainRequire = decl.id && (
  decl.id.type === 'Identifier' || decl.id.type === 'ObjectPattern') &&
  isRequireExpression(decl.init);
  var isRequireWithMemberExpression = decl.id && (
  decl.id.type === 'Identifier' || decl.id.type === 'ObjectPattern') &&
  decl.init != null &&
  decl.init.type === 'CallExpression' &&
  decl.init.callee != null &&
  decl.init.callee.type === 'MemberExpression' &&
  isRequireExpression(decl.init.callee.object);
  return isPlainRequire || isRequireWithMemberExpression;
}

function isPlainImportModule(node) {
  return node.type === 'ImportDeclaration' && node.specifiers != null && node.specifiers.length > 0;
}

function isPlainImportEquals(node) {
  return node.type === 'TSImportEqualsDeclaration' && node.moduleReference.expression;
}

function isCJSExports(context, node) {
  if (
  node.type === 'MemberExpression' &&
  node.object.type === 'Identifier' &&
  node.property.type === 'Identifier' &&
  node.object.name === 'module' &&
  node.property.name === 'exports')
  {
    return (0, _contextCompat.getScope)(context, node).variables.findIndex(function (variable) {return variable.name === 'module';}) === -1;
  }
  if (
  node.type === 'Identifier' &&
  node.name === 'exports')
  {
    return (0, _contextCompat.getScope)(context, node).variables.findIndex(function (variable) {return variable.name === 'exports';}) === -1;
  }
}

function getNamedCJSExports(context, node) {
  if (node.type !== 'MemberExpression') {
    return;
  }
  var result = [];
  var root = node;
  var parent = null;
  while (root.type === 'MemberExpression') {
    if (root.property.type !== 'Identifier') {
      return;
    }
    result.unshift(root.property.name);
    parent = root;
    root = root.object;
  }

  if (isCJSExports(context, root)) {
    return result;
  }

  if (isCJSExports(context, parent)) {
    return result.slice(1);
  }
}

function canCrossNodeWhileReorder(node) {
  return isSupportedRequireModule(node) || isPlainImportModule(node) || isPlainImportEquals(node);
}

function canReorderItems(firstNode, secondNode) {
  var parent = firstNode.parent;var _sort =
  [
  parent.body.indexOf(firstNode),
  parent.body.indexOf(secondNode)].
  sort(),_sort2 = _slicedToArray(_sort, 2),firstIndex = _sort2[0],secondIndex = _sort2[1];
  var nodesBetween = parent.body.slice(firstIndex, secondIndex + 1);var _iteratorNormalCompletion = true;var _didIteratorError = false;var _iteratorError = undefined;try {
    for (var _iterator = nodesBetween[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {var nodeBetween = _step.value;
      if (!canCrossNodeWhileReorder(nodeBetween)) {
        return false;
      }
    }} catch (err) {_didIteratorError = true;_iteratorError = err;} finally {try {if (!_iteratorNormalCompletion && _iterator['return']) {_iterator['return']();}} finally {if (_didIteratorError) {throw _iteratorError;}}}
  return true;
}

function makeImportDescription(node) {
  if (node.type === 'export') {
    if (node.node.exportKind === 'type') {
      return 'type export';
    }
    return 'export';
  }
  if (node.node.importKind === 'type') {
    return 'type import';
  }
  if (node.node.importKind === 'typeof') {
    return 'typeof import';
  }
  return 'import';
}

function fixOutOfOrder(context, firstNode, secondNode, order, category) {
  var isNamed = category === categories.named;
  var isExports = category === categories.exports;
  var sourceCode = (0, _contextCompat.getSourceCode)(context);var _ref =




  isNamed ? {
    firstRoot: firstNode.node,
    secondRoot: secondNode.node } :
  {
    firstRoot: findRootNode(firstNode.node),
    secondRoot: findRootNode(secondNode.node) },firstRoot = _ref.firstRoot,secondRoot = _ref.secondRoot;var _ref2 =







  isNamed ? {
    firstRootStart: findSpecifierStart(sourceCode, firstRoot),
    firstRootEnd: findSpecifierEnd(sourceCode, firstRoot),
    secondRootStart: findSpecifierStart(sourceCode, secondRoot),
    secondRootEnd: findSpecifierEnd(sourceCode, secondRoot) } :
  {
    firstRootStart: findStartOfLineWithComments(sourceCode, firstRoot),
    firstRootEnd: findEndOfLineWithComments(sourceCode, firstRoot),
    secondRootStart: findStartOfLineWithComments(sourceCode, secondRoot),
    secondRootEnd: findEndOfLineWithComments(sourceCode, secondRoot) },firstRootStart = _ref2.firstRootStart,firstRootEnd = _ref2.firstRootEnd,secondRootStart = _ref2.secondRootStart,secondRootEnd = _ref2.secondRootEnd;


  if (firstNode.displayName === secondNode.displayName) {
    if (firstNode.alias) {
      firstNode.displayName = String(firstNode.displayName) + ' as ' + String(firstNode.alias);
    }
    if (secondNode.alias) {
      secondNode.displayName = String(secondNode.displayName) + ' as ' + String(secondNode.alias);
    }
  }

  var firstImport = String(makeImportDescription(firstNode)) + ' of `' + String(firstNode.displayName) + '`';
  var secondImport = '`' + String(secondNode.displayName) + '` ' + String(makeImportDescription(secondNode));
  var message = secondImport + ' should occur ' + String(order) + ' ' + firstImport;

  if (isNamed) {
    var firstCode = sourceCode.text.slice(firstRootStart, firstRoot.range[1]);
    var firstTrivia = sourceCode.text.slice(firstRoot.range[1], firstRootEnd);
    var secondCode = sourceCode.text.slice(secondRootStart, secondRoot.range[1]);
    var secondTrivia = sourceCode.text.slice(secondRoot.range[1], secondRootEnd);

    if (order === 'before') {
      var trimmedTrivia = (0, _stringPrototype2['default'])(secondTrivia);
      var gapCode = sourceCode.text.slice(firstRootEnd, secondRootStart - 1);
      var whitespaces = secondTrivia.slice(trimmedTrivia.length);
      context.report({
        node: secondNode.node,
        message: message,
        fix: function () {function fix(fixer) {return fixer.replaceTextRange(
            [firstRootStart, secondRootEnd], String(
            secondCode) + ',' + String(trimmedTrivia) + String(firstCode) + String(firstTrivia) + String(gapCode) + String(whitespaces));}return fix;}() });


    } else if (order === 'after') {
      var _trimmedTrivia = (0, _stringPrototype2['default'])(firstTrivia);
      var _gapCode = sourceCode.text.slice(secondRootEnd + 1, firstRootStart);
      var _whitespaces = firstTrivia.slice(_trimmedTrivia.length);
      context.report({
        node: secondNode.node,
        message: message,
        fix: function () {function fix(fixes) {return fixes.replaceTextRange(
            [secondRootStart, firstRootEnd], '' + String(
            _gapCode) + String(firstCode) + ',' + String(_trimmedTrivia) + String(secondCode) + String(_whitespaces));}return fix;}() });


    }
  } else {
    var canFix = isExports || canReorderItems(firstRoot, secondRoot);
    var newCode = sourceCode.text.substring(secondRootStart, secondRootEnd);

    if (newCode[newCode.length - 1] !== '\n') {
      newCode = String(newCode) + '\n';
    }

    if (order === 'before') {
      context.report({
        node: secondNode.node,
        message: message,
        fix: canFix && function (fixer) {return fixer.replaceTextRange(
          [firstRootStart, secondRootEnd],
          newCode + sourceCode.text.substring(firstRootStart, secondRootStart));} });


    } else if (order === 'after') {
      context.report({
        node: secondNode.node,
        message: message,
        fix: canFix && function (fixer) {return fixer.replaceTextRange(
          [secondRootStart, firstRootEnd],
          sourceCode.text.substring(secondRootEnd, firstRootEnd) + newCode);} });


    }
  }
}

function reportOutOfOrder(context, imported, outOfOrder, order, category) {
  outOfOrder.forEach(function (imp) {
    var found = imported.find(function () {function hasHigherRank(importedItem) {
        return importedItem.rank > imp.rank;
      }return hasHigherRank;}());
    fixOutOfOrder(context, found, imp, order, category);
  });
}

function makeOutOfOrderReport(context, imported, category) {
  var outOfOrder = findOutOfOrder(imported);
  if (!outOfOrder.length) {
    return;
  }

  // There are things to report. Try to minimize the number of reported errors.
  var reversedImported = reverse(imported);
  var reversedOrder = findOutOfOrder(reversedImported);
  if (reversedOrder.length < outOfOrder.length) {
    reportOutOfOrder(context, reversedImported, reversedOrder, 'after', category);
    return;
  }
  reportOutOfOrder(context, imported, outOfOrder, 'before', category);
}

var compareString = function compareString(a, b) {
  if (a < b) {
    return -1;
  }
  if (a > b) {
    return 1;
  }
  return 0;
};

/** Some parsers (languages without types) don't provide ImportKind */
var DEAFULT_IMPORT_KIND = 'value';
var getNormalizedValue = function getNormalizedValue(node, toLowerCase) {
  var value = node.value;
  return toLowerCase ? String(value).toLowerCase() : value;
};

function getSorter(alphabetizeOptions) {
  var multiplier = alphabetizeOptions.order === 'asc' ? 1 : -1;
  var orderImportKind = alphabetizeOptions.orderImportKind;
  var multiplierImportKind = orderImportKind !== 'ignore' && (
  alphabetizeOptions.orderImportKind === 'asc' ? 1 : -1);

  return function () {function importsSorter(nodeA, nodeB) {
      var importA = getNormalizedValue(nodeA, alphabetizeOptions.caseInsensitive);
      var importB = getNormalizedValue(nodeB, alphabetizeOptions.caseInsensitive);
      var result = 0;

      if (!(0, _arrayIncludes2['default'])(importA, '/') && !(0, _arrayIncludes2['default'])(importB, '/')) {
        result = compareString(importA, importB);
      } else {
        var A = importA.split('/');
        var B = importB.split('/');
        var a = A.length;
        var b = B.length;

        for (var i = 0; i < Math.min(a, b); i++) {
          // Skip comparing the first path segment, if they are relative segments for both imports
          if (i === 0 && (A[i] === '.' || A[i] === '..') && (B[i] === '.' || B[i] === '..')) {
            // If one is sibling and the other parent import, no need to compare at all, since the paths belong in different groups
            if (A[i] !== B[i]) {break;}
            continue;
          }
          result = compareString(A[i], B[i]);
          if (result) {break;}
        }

        if (!result && a !== b) {
          result = a < b ? -1 : 1;
        }
      }

      result = result * multiplier;

      // In case the paths are equal (result === 0), sort them by importKind
      if (!result && multiplierImportKind) {
        result = multiplierImportKind * compareString(
        nodeA.node.importKind || DEAFULT_IMPORT_KIND,
        nodeB.node.importKind || DEAFULT_IMPORT_KIND);

      }

      return result;
    }return importsSorter;}();
}

function mutateRanksToAlphabetize(imported, alphabetizeOptions) {
  var groupedByRanks = (0, _object2['default'])(imported, function (item) {return item.rank;});

  var sorterFn = getSorter(alphabetizeOptions);

  // sort group keys so that they can be iterated on in order
  var groupRanks = Object.keys(groupedByRanks).sort(function (a, b) {
    return a - b;
  });

  // sort imports locally within their group
  groupRanks.forEach(function (groupRank) {
    groupedByRanks[groupRank].sort(sorterFn);
  });

  // assign globally unique rank to each import
  var newRank = 0;
  var alphabetizedRanks = groupRanks.reduce(function (acc, groupRank) {
    groupedByRanks[groupRank].forEach(function (importedItem) {
      acc[String(importedItem.value) + '|' + String(importedItem.node.importKind)] = parseInt(groupRank, 10) + newRank;
      newRank += 1;
    });
    return acc;
  }, {});

  // mutate the original group-rank with alphabetized-rank
  imported.forEach(function (importedItem) {
    importedItem.rank = alphabetizedRanks[String(importedItem.value) + '|' + String(importedItem.node.importKind)];
  });
}

// DETECTING

function computePathRank(ranks, pathGroups, path, maxPosition) {
  for (var i = 0, l = pathGroups.length; i < l; i++) {var _pathGroups$i =
    pathGroups[i],pattern = _pathGroups$i.pattern,patternOptions = _pathGroups$i.patternOptions,group = _pathGroups$i.group,_pathGroups$i$positio = _pathGroups$i.position,position = _pathGroups$i$positio === undefined ? 1 : _pathGroups$i$positio;
    if ((0, _minimatch2['default'])(path, pattern, patternOptions || { nocomment: true })) {
      return ranks[group] + position / maxPosition;
    }
  }
}

function computeRank(context, ranks, importEntry, excludedImportTypes) {
  var impType = void 0;
  var rank = void 0;
  if (importEntry.type === 'import:object') {
    impType = 'object';
  } else if (importEntry.node.importKind === 'type' && ranks.omittedTypes.indexOf('type') === -1) {
    impType = 'type';
  } else {
    impType = (0, _importType2['default'])(importEntry.value, context);
  }
  if (!excludedImportTypes.has(impType)) {
    rank = computePathRank(ranks.groups, ranks.pathGroups, importEntry.value, ranks.maxPosition);
  }
  if (typeof rank === 'undefined') {
    rank = ranks.groups[impType];
  }
  if (importEntry.type !== 'import' && !importEntry.type.startsWith('import:')) {
    rank += 100;
  }

  return rank;
}

function registerNode(context, importEntry, ranks, imported, excludedImportTypes) {
  var rank = computeRank(context, ranks, importEntry, excludedImportTypes);
  if (rank !== -1) {
    imported.push(Object.assign({}, importEntry, { rank: rank }));
  }
}

function getRequireBlock(node) {
  var n = node;
  // Handle cases like `const baz = require('foo').bar.baz`
  // and `const foo = require('foo')()`
  while (
  n.parent.type === 'MemberExpression' && n.parent.object === n ||
  n.parent.type === 'CallExpression' && n.parent.callee === n)
  {
    n = n.parent;
  }
  if (
  n.parent.type === 'VariableDeclarator' &&
  n.parent.parent.type === 'VariableDeclaration' &&
  n.parent.parent.parent.type === 'Program')
  {
    return n.parent.parent.parent;
  }
}

var types = ['builtin', 'external', 'internal', 'unknown', 'parent', 'sibling', 'index', 'object', 'type'];

// Creates an object with type-rank pairs.
// Example: { index: 0, sibling: 1, parent: 1, external: 1, builtin: 2, internal: 2 }
// Will throw an error if it contains a type that does not exist, or has a duplicate
function convertGroupsToRanks(groups) {
  var rankObject = groups.reduce(function (res, group, index) {
    [].concat(group).forEach(function (groupItem) {
      if (types.indexOf(groupItem) === -1) {
        throw new Error('Incorrect configuration of the rule: Unknown type `' + String(JSON.stringify(groupItem)) + '`');
      }
      if (res[groupItem] !== undefined) {
        throw new Error('Incorrect configuration of the rule: `' + String(groupItem) + '` is duplicated');
      }
      res[groupItem] = index * 2;
    });
    return res;
  }, {});

  var omittedTypes = types.filter(function (type) {
    return typeof rankObject[type] === 'undefined';
  });

  var ranks = omittedTypes.reduce(function (res, type) {
    res[type] = groups.length * 2;
    return res;
  }, rankObject);

  return { groups: ranks, omittedTypes: omittedTypes };
}

function convertPathGroupsForRanks(pathGroups) {
  var after = {};
  var before = {};

  var transformed = pathGroups.map(function (pathGroup, index) {var
    group = pathGroup.group,positionString = pathGroup.position;
    var position = 0;
    if (positionString === 'after') {
      if (!after[group]) {
        after[group] = 1;
      }
      position = after[group]++;
    } else if (positionString === 'before') {
      if (!before[group]) {
        before[group] = [];
      }
      before[group].push(index);
    }

    return Object.assign({}, pathGroup, { position: position });
  });

  var maxPosition = 1;

  Object.keys(before).forEach(function (group) {
    var groupLength = before[group].length;
    before[group].forEach(function (groupIndex, index) {
      transformed[groupIndex].position = -1 * (groupLength - index);
    });
    maxPosition = Math.max(maxPosition, groupLength);
  });

  Object.keys(after).forEach(function (key) {
    var groupNextPosition = after[key];
    maxPosition = Math.max(maxPosition, groupNextPosition - 1);
  });

  return {
    pathGroups: transformed,
    maxPosition: maxPosition > 10 ? Math.pow(10, Math.ceil(Math.log10(maxPosition))) : 10 };

}

function fixNewLineAfterImport(context, previousImport) {
  var prevRoot = findRootNode(previousImport.node);
  var tokensToEndOfLine = takeTokensAfterWhile(
  (0, _contextCompat.getSourceCode)(context),
  prevRoot,
  commentOnSameLineAs(prevRoot));


  var endOfLine = prevRoot.range[1];
  if (tokensToEndOfLine.length > 0) {
    endOfLine = tokensToEndOfLine[tokensToEndOfLine.length - 1].range[1];
  }
  return function (fixer) {return fixer.insertTextAfterRange([prevRoot.range[0], endOfLine], '\n');};
}

function removeNewLineAfterImport(context, currentImport, previousImport) {
  var sourceCode = (0, _contextCompat.getSourceCode)(context);
  var prevRoot = findRootNode(previousImport.node);
  var currRoot = findRootNode(currentImport.node);
  var rangeToRemove = [
  findEndOfLineWithComments(sourceCode, prevRoot),
  findStartOfLineWithComments(sourceCode, currRoot)];

  if (/^\s*$/.test(sourceCode.text.substring(rangeToRemove[0], rangeToRemove[1]))) {
    return function (fixer) {return fixer.removeRange(rangeToRemove);};
  }
  return undefined;
}

function makeNewlinesBetweenReport(context, imported, newlinesBetweenImports, distinctGroup) {
  var getNumberOfEmptyLinesBetween = function getNumberOfEmptyLinesBetween(currentImport, previousImport) {
    var linesBetweenImports = (0, _contextCompat.getSourceCode)(context).lines.slice(
    previousImport.node.loc.end.line,
    currentImport.node.loc.start.line - 1);


    return linesBetweenImports.filter(function (line) {return !line.trim().length;}).length;
  };
  var getIsStartOfDistinctGroup = function getIsStartOfDistinctGroup(currentImport, previousImport) {return currentImport.rank - 1 >= previousImport.rank;};
  var previousImport = imported[0];

  imported.slice(1).forEach(function (currentImport) {
    var emptyLinesBetween = getNumberOfEmptyLinesBetween(currentImport, previousImport);
    var isStartOfDistinctGroup = getIsStartOfDistinctGroup(currentImport, previousImport);

    if (newlinesBetweenImports === 'always' ||
    newlinesBetweenImports === 'always-and-inside-groups') {
      if (currentImport.rank !== previousImport.rank && emptyLinesBetween === 0) {
        if (distinctGroup || !distinctGroup && isStartOfDistinctGroup) {
          context.report({
            node: previousImport.node,
            message: 'There should be at least one empty line between import groups',
            fix: fixNewLineAfterImport(context, previousImport) });

        }
      } else if (emptyLinesBetween > 0 &&
      newlinesBetweenImports !== 'always-and-inside-groups') {
        if (distinctGroup && currentImport.rank === previousImport.rank || !distinctGroup && !isStartOfDistinctGroup) {
          context.report({
            node: previousImport.node,
            message: 'There should be no empty line within import group',
            fix: removeNewLineAfterImport(context, currentImport, previousImport) });

        }
      }
    } else if (emptyLinesBetween > 0) {
      context.report({
        node: previousImport.node,
        message: 'There should be no empty line between import groups',
        fix: removeNewLineAfterImport(context, currentImport, previousImport) });

    }

    previousImport = currentImport;
  });
}

function getAlphabetizeConfig(options) {
  var alphabetize = options.alphabetize || {};
  var order = alphabetize.order || 'ignore';
  var orderImportKind = alphabetize.orderImportKind || 'ignore';
  var caseInsensitive = alphabetize.caseInsensitive || false;

  return { order: order, orderImportKind: orderImportKind, caseInsensitive: caseInsensitive };
}

// TODO, semver-major: Change the default of "distinctGroup" from true to false
var defaultDistinctGroup = true;

module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      category: 'Style guide',
      description: 'Enforce a convention in module import order.',
      url: (0, _docsUrl2['default'])('order') },


    fixable: 'code',
    schema: [
    {
      type: 'object',
      properties: {
        groups: {
          type: 'array' },

        pathGroupsExcludedImportTypes: {
          type: 'array' },

        distinctGroup: {
          type: 'boolean',
          'default': defaultDistinctGroup },

        pathGroups: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              pattern: {
                type: 'string' },

              patternOptions: {
                type: 'object' },

              group: {
                type: 'string',
                'enum': types },

              position: {
                type: 'string',
                'enum': ['after', 'before'] } },


            additionalProperties: false,
            required: ['pattern', 'group'] } },


        'newlines-between': {
          'enum': [
          'ignore',
          'always',
          'always-and-inside-groups',
          'never'] },


        named: {
          'default': false,
          oneOf: [{
            type: 'boolean' },
          {
            type: 'object',
            properties: {
              enabled: { type: 'boolean' },
              'import': { type: 'boolean' },
              'export': { type: 'boolean' },
              require: { type: 'boolean' },
              cjsExports: { type: 'boolean' },
              types: {
                type: 'string',
                'enum': [
                'mixed',
                'types-first',
                'types-last'] } },



            additionalProperties: false }] },


        alphabetize: {
          type: 'object',
          properties: {
            caseInsensitive: {
              type: 'boolean',
              'default': false },

            order: {
              'enum': ['ignore', 'asc', 'desc'],
              'default': 'ignore' },

            orderImportKind: {
              'enum': ['ignore', 'asc', 'desc'],
              'default': 'ignore' } },


          additionalProperties: false },

        warnOnUnassignedImports: {
          type: 'boolean',
          'default': false } },


      additionalProperties: false }] },




  create: function () {function create(context) {
      var options = context.options[0] || {};
      var newlinesBetweenImports = options['newlines-between'] || 'ignore';
      var pathGroupsExcludedImportTypes = new Set(options.pathGroupsExcludedImportTypes || ['builtin', 'external', 'object']);

      var named = Object.assign({
        types: 'mixed' },
      _typeof(options.named) === 'object' ? Object.assign({},
      options.named, {
        'import': 'import' in options.named ? options.named['import'] : options.named.enabled,
        'export': 'export' in options.named ? options.named['export'] : options.named.enabled,
        require: 'require' in options.named ? options.named.require : options.named.enabled,
        cjsExports: 'cjsExports' in options.named ? options.named.cjsExports : options.named.enabled }) :
      {
        'import': options.named,
        'export': options.named,
        require: options.named,
        cjsExports: options.named });



      var namedGroups = named.types === 'mixed' ? [] : named.types === 'types-last' ? ['value'] : ['type'];
      var alphabetize = getAlphabetizeConfig(options);
      var distinctGroup = options.distinctGroup == null ? defaultDistinctGroup : !!options.distinctGroup;
      var ranks = void 0;

      try {var _convertPathGroupsFor =
        convertPathGroupsForRanks(options.pathGroups || []),pathGroups = _convertPathGroupsFor.pathGroups,maxPosition = _convertPathGroupsFor.maxPosition;var _convertGroupsToRanks =
        convertGroupsToRanks(options.groups || defaultGroups),groups = _convertGroupsToRanks.groups,omittedTypes = _convertGroupsToRanks.omittedTypes;
        ranks = {
          groups: groups,
          omittedTypes: omittedTypes,
          pathGroups: pathGroups,
          maxPosition: maxPosition };

      } catch (error) {
        // Malformed configuration
        return {
          Program: function () {function Program(node) {
              context.report(node, error.message);
            }return Program;}() };

      }
      var importMap = new Map();
      var exportMap = new Map();

      function getBlockImports(node) {
        if (!importMap.has(node)) {
          importMap.set(node, []);
        }
        return importMap.get(node);
      }

      function getBlockExports(node) {
        if (!exportMap.has(node)) {
          exportMap.set(node, []);
        }
        return exportMap.get(node);
      }

      function makeNamedOrderReport(context, namedImports) {
        if (namedImports.length > 1) {
          var imports = namedImports.map(
          function (namedImport) {
            var kind = namedImport.kind || 'value';
            var rank = namedGroups.findIndex(function (entry) {return [].concat(entry).indexOf(kind) > -1;});

            return Object.assign({
              displayName: namedImport.value,
              rank: rank === -1 ? namedGroups.length : rank },
            namedImport, {
              value: String(namedImport.value) + ':' + String(namedImport.alias || '') });

          });

          if (alphabetize.order !== 'ignore') {
            mutateRanksToAlphabetize(imports, alphabetize);
          }

          makeOutOfOrderReport(context, imports, categories.named);
        }
      }

      return Object.assign({
        ImportDeclaration: function () {function ImportDeclaration(node) {
            // Ignoring unassigned imports unless warnOnUnassignedImports is set
            if (node.specifiers.length || options.warnOnUnassignedImports) {
              var name = node.source.value;
              registerNode(
              context,
              {
                node: node,
                value: name,
                displayName: name,
                type: 'import' },

              ranks,
              getBlockImports(node.parent),
              pathGroupsExcludedImportTypes);


              if (named['import']) {
                makeNamedOrderReport(
                context,
                node.specifiers.filter(
                function (specifier) {return specifier.type === 'ImportSpecifier';}).map(
                function (specifier) {return Object.assign({
                    node: specifier,
                    value: specifier.imported.name,
                    type: 'import',
                    kind: specifier.importKind },
                  specifier.local.range[0] !== specifier.imported.range[0] && {
                    alias: specifier.local.name });}));




              }
            }
          }return ImportDeclaration;}(),
        TSImportEqualsDeclaration: function () {function TSImportEqualsDeclaration(node) {
            // skip "export import"s
            if (node.isExport) {
              return;
            }

            var displayName = void 0;
            var value = void 0;
            var type = void 0;
            if (node.moduleReference.type === 'TSExternalModuleReference') {
              value = node.moduleReference.expression.value;
              displayName = value;
              type = 'import';
            } else {
              value = '';
              displayName = (0, _contextCompat.getSourceCode)(context).getText(node.moduleReference);
              type = 'import:object';
            }

            registerNode(
            context,
            {
              node: node,
              value: value,
              displayName: displayName,
              type: type },

            ranks,
            getBlockImports(node.parent),
            pathGroupsExcludedImportTypes);

          }return TSImportEqualsDeclaration;}(),
        CallExpression: function () {function CallExpression(node) {
            if (!(0, _staticRequire2['default'])(node)) {
              return;
            }
            var block = getRequireBlock(node);
            if (!block) {
              return;
            }
            var name = node.arguments[0].value;
            registerNode(
            context,
            {
              node: node,
              value: name,
              displayName: name,
              type: 'require' },

            ranks,
            getBlockImports(block),
            pathGroupsExcludedImportTypes);

          }return CallExpression;}() },
      named.require && {
        VariableDeclarator: function () {function VariableDeclarator(node) {
            if (node.id.type === 'ObjectPattern' && isRequireExpression(node.init)) {
              for (var i = 0; i < node.id.properties.length; i++) {
                if (
                node.id.properties[i].key.type !== 'Identifier' ||
                node.id.properties[i].value.type !== 'Identifier')
                {
                  return;
                }
              }
              makeNamedOrderReport(
              context,
              node.id.properties.map(function (prop) {return Object.assign({
                  node: prop,
                  value: prop.key.name,
                  type: 'require' },
                prop.key.range[0] !== prop.value.range[0] && {
                  alias: prop.value.name });}));



            }
          }return VariableDeclarator;}() },

      named['export'] && {
        ExportNamedDeclaration: function () {function ExportNamedDeclaration(node) {
            makeNamedOrderReport(
            context,
            node.specifiers.map(function (specifier) {return Object.assign({
                node: specifier,
                value: specifier.local.name,
                type: 'export',
                kind: specifier.exportKind },
              specifier.local.range[0] !== specifier.exported.range[0] && {
                alias: specifier.exported.name });}));



          }return ExportNamedDeclaration;}() },

      named.cjsExports && {
        AssignmentExpression: function () {function AssignmentExpression(node) {
            if (node.parent.type === 'ExpressionStatement') {
              if (isCJSExports(context, node.left)) {
                if (node.right.type === 'ObjectExpression') {
                  for (var i = 0; i < node.right.properties.length; i++) {
                    if (
                    node.right.properties[i].key.type !== 'Identifier' ||
                    node.right.properties[i].value.type !== 'Identifier')
                    {
                      return;
                    }
                  }

                  makeNamedOrderReport(
                  context,
                  node.right.properties.map(function (prop) {return Object.assign({
                      node: prop,
                      value: prop.key.name,
                      type: 'export' },
                    prop.key.range[0] !== prop.value.range[0] && {
                      alias: prop.value.name });}));



                }
              } else {
                var nameParts = getNamedCJSExports(context, node.left);
                if (nameParts && nameParts.length > 0) {
                  var name = nameParts.join('.');
                  getBlockExports(node.parent.parent).push({
                    node: node,
                    value: name,
                    displayName: name,
                    type: 'export',
                    rank: 0 });

                }
              }
            }
          }return AssignmentExpression;}() }, {

        'Program:exit': function () {function ProgramExit() {
            importMap.forEach(function (imported) {
              if (newlinesBetweenImports !== 'ignore') {
                makeNewlinesBetweenReport(context, imported, newlinesBetweenImports, distinctGroup);
              }

              if (alphabetize.order !== 'ignore') {
                mutateRanksToAlphabetize(imported, alphabetize);
              }

              makeOutOfOrderReport(context, imported, categories['import']);
            });

            exportMap.forEach(function (exported) {
              if (alphabetize.order !== 'ignore') {
                mutateRanksToAlphabetize(exported, alphabetize);
                makeOutOfOrderReport(context, exported, categories.exports);
              }
            });

            importMap.clear();
            exportMap.clear();
          }return ProgramExit;}() });

    }return create;}() };
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi4uLy4uL3NyYy9ydWxlcy9vcmRlci5qcyJdLCJuYW1lcyI6WyJjYXRlZ29yaWVzIiwibmFtZWQiLCJleHBvcnRzIiwiZGVmYXVsdEdyb3VwcyIsInJldmVyc2UiLCJhcnJheSIsIm1hcCIsInYiLCJyYW5rIiwiZ2V0VG9rZW5zT3JDb21tZW50c0FmdGVyIiwic291cmNlQ29kZSIsIm5vZGUiLCJjb3VudCIsImN1cnJlbnROb2RlT3JUb2tlbiIsInJlc3VsdCIsImkiLCJnZXRUb2tlbk9yQ29tbWVudEFmdGVyIiwicHVzaCIsImdldFRva2Vuc09yQ29tbWVudHNCZWZvcmUiLCJnZXRUb2tlbk9yQ29tbWVudEJlZm9yZSIsInRha2VUb2tlbnNBZnRlcldoaWxlIiwiY29uZGl0aW9uIiwidG9rZW5zIiwibGVuZ3RoIiwidGFrZVRva2Vuc0JlZm9yZVdoaWxlIiwiZmluZE91dE9mT3JkZXIiLCJpbXBvcnRlZCIsIm1heFNlZW5SYW5rTm9kZSIsImZpbHRlciIsImltcG9ydGVkTW9kdWxlIiwicmVzIiwiZmluZFJvb3ROb2RlIiwicGFyZW50IiwiYm9keSIsImNvbW1lbnRPblNhbWVMaW5lQXMiLCJ0b2tlbiIsInR5cGUiLCJsb2MiLCJzdGFydCIsImxpbmUiLCJlbmQiLCJmaW5kRW5kT2ZMaW5lV2l0aENvbW1lbnRzIiwidG9rZW5zVG9FbmRPZkxpbmUiLCJlbmRPZlRva2VucyIsInJhbmdlIiwidGV4dCIsImZpbmRTdGFydE9mTGluZVdpdGhDb21tZW50cyIsInN0YXJ0T2ZUb2tlbnMiLCJmaW5kU3BlY2lmaWVyU3RhcnQiLCJnZXRUb2tlbkJlZm9yZSIsInZhbHVlIiwiZmluZFNwZWNpZmllckVuZCIsImdldFRva2VuQWZ0ZXIiLCJpc1JlcXVpcmVFeHByZXNzaW9uIiwiZXhwciIsImNhbGxlZSIsIm5hbWUiLCJhcmd1bWVudHMiLCJpc1N1cHBvcnRlZFJlcXVpcmVNb2R1bGUiLCJkZWNsYXJhdGlvbnMiLCJkZWNsIiwiaXNQbGFpblJlcXVpcmUiLCJpZCIsImluaXQiLCJpc1JlcXVpcmVXaXRoTWVtYmVyRXhwcmVzc2lvbiIsIm9iamVjdCIsImlzUGxhaW5JbXBvcnRNb2R1bGUiLCJzcGVjaWZpZXJzIiwiaXNQbGFpbkltcG9ydEVxdWFscyIsIm1vZHVsZVJlZmVyZW5jZSIsImV4cHJlc3Npb24iLCJpc0NKU0V4cG9ydHMiLCJjb250ZXh0IiwicHJvcGVydHkiLCJ2YXJpYWJsZXMiLCJmaW5kSW5kZXgiLCJ2YXJpYWJsZSIsImdldE5hbWVkQ0pTRXhwb3J0cyIsInJvb3QiLCJ1bnNoaWZ0Iiwic2xpY2UiLCJjYW5Dcm9zc05vZGVXaGlsZVJlb3JkZXIiLCJjYW5SZW9yZGVySXRlbXMiLCJmaXJzdE5vZGUiLCJzZWNvbmROb2RlIiwiaW5kZXhPZiIsInNvcnQiLCJmaXJzdEluZGV4Iiwic2Vjb25kSW5kZXgiLCJub2Rlc0JldHdlZW4iLCJub2RlQmV0d2VlbiIsIm1ha2VJbXBvcnREZXNjcmlwdGlvbiIsImV4cG9ydEtpbmQiLCJpbXBvcnRLaW5kIiwiZml4T3V0T2ZPcmRlciIsIm9yZGVyIiwiY2F0ZWdvcnkiLCJpc05hbWVkIiwiaXNFeHBvcnRzIiwiZmlyc3RSb290Iiwic2Vjb25kUm9vdCIsImZpcnN0Um9vdFN0YXJ0IiwiZmlyc3RSb290RW5kIiwic2Vjb25kUm9vdFN0YXJ0Iiwic2Vjb25kUm9vdEVuZCIsImRpc3BsYXlOYW1lIiwiYWxpYXMiLCJmaXJzdEltcG9ydCIsInNlY29uZEltcG9ydCIsIm1lc3NhZ2UiLCJmaXJzdENvZGUiLCJmaXJzdFRyaXZpYSIsInNlY29uZENvZGUiLCJzZWNvbmRUcml2aWEiLCJ0cmltbWVkVHJpdmlhIiwiZ2FwQ29kZSIsIndoaXRlc3BhY2VzIiwicmVwb3J0IiwiZml4IiwiZml4ZXIiLCJyZXBsYWNlVGV4dFJhbmdlIiwiZml4ZXMiLCJjYW5GaXgiLCJuZXdDb2RlIiwic3Vic3RyaW5nIiwicmVwb3J0T3V0T2ZPcmRlciIsIm91dE9mT3JkZXIiLCJmb3JFYWNoIiwiaW1wIiwiZm91bmQiLCJmaW5kIiwiaGFzSGlnaGVyUmFuayIsImltcG9ydGVkSXRlbSIsIm1ha2VPdXRPZk9yZGVyUmVwb3J0IiwicmV2ZXJzZWRJbXBvcnRlZCIsInJldmVyc2VkT3JkZXIiLCJjb21wYXJlU3RyaW5nIiwiYSIsImIiLCJERUFGVUxUX0lNUE9SVF9LSU5EIiwiZ2V0Tm9ybWFsaXplZFZhbHVlIiwidG9Mb3dlckNhc2UiLCJTdHJpbmciLCJnZXRTb3J0ZXIiLCJhbHBoYWJldGl6ZU9wdGlvbnMiLCJtdWx0aXBsaWVyIiwib3JkZXJJbXBvcnRLaW5kIiwibXVsdGlwbGllckltcG9ydEtpbmQiLCJpbXBvcnRzU29ydGVyIiwibm9kZUEiLCJub2RlQiIsImltcG9ydEEiLCJjYXNlSW5zZW5zaXRpdmUiLCJpbXBvcnRCIiwiQSIsInNwbGl0IiwiQiIsIk1hdGgiLCJtaW4iLCJtdXRhdGVSYW5rc1RvQWxwaGFiZXRpemUiLCJncm91cGVkQnlSYW5rcyIsIml0ZW0iLCJzb3J0ZXJGbiIsImdyb3VwUmFua3MiLCJPYmplY3QiLCJrZXlzIiwiZ3JvdXBSYW5rIiwibmV3UmFuayIsImFscGhhYmV0aXplZFJhbmtzIiwicmVkdWNlIiwiYWNjIiwicGFyc2VJbnQiLCJjb21wdXRlUGF0aFJhbmsiLCJyYW5rcyIsInBhdGhHcm91cHMiLCJwYXRoIiwibWF4UG9zaXRpb24iLCJsIiwicGF0dGVybiIsInBhdHRlcm5PcHRpb25zIiwiZ3JvdXAiLCJwb3NpdGlvbiIsIm5vY29tbWVudCIsImNvbXB1dGVSYW5rIiwiaW1wb3J0RW50cnkiLCJleGNsdWRlZEltcG9ydFR5cGVzIiwiaW1wVHlwZSIsIm9taXR0ZWRUeXBlcyIsImhhcyIsImdyb3VwcyIsInN0YXJ0c1dpdGgiLCJyZWdpc3Rlck5vZGUiLCJnZXRSZXF1aXJlQmxvY2siLCJuIiwidHlwZXMiLCJjb252ZXJ0R3JvdXBzVG9SYW5rcyIsInJhbmtPYmplY3QiLCJpbmRleCIsImNvbmNhdCIsImdyb3VwSXRlbSIsIkVycm9yIiwiSlNPTiIsInN0cmluZ2lmeSIsInVuZGVmaW5lZCIsImNvbnZlcnRQYXRoR3JvdXBzRm9yUmFua3MiLCJhZnRlciIsImJlZm9yZSIsInRyYW5zZm9ybWVkIiwicGF0aEdyb3VwIiwicG9zaXRpb25TdHJpbmciLCJncm91cExlbmd0aCIsImdyb3VwSW5kZXgiLCJtYXgiLCJrZXkiLCJncm91cE5leHRQb3NpdGlvbiIsInBvdyIsImNlaWwiLCJsb2cxMCIsImZpeE5ld0xpbmVBZnRlckltcG9ydCIsInByZXZpb3VzSW1wb3J0IiwicHJldlJvb3QiLCJlbmRPZkxpbmUiLCJpbnNlcnRUZXh0QWZ0ZXJSYW5nZSIsInJlbW92ZU5ld0xpbmVBZnRlckltcG9ydCIsImN1cnJlbnRJbXBvcnQiLCJjdXJyUm9vdCIsInJhbmdlVG9SZW1vdmUiLCJ0ZXN0IiwicmVtb3ZlUmFuZ2UiLCJtYWtlTmV3bGluZXNCZXR3ZWVuUmVwb3J0IiwibmV3bGluZXNCZXR3ZWVuSW1wb3J0cyIsImRpc3RpbmN0R3JvdXAiLCJnZXROdW1iZXJPZkVtcHR5TGluZXNCZXR3ZWVuIiwibGluZXNCZXR3ZWVuSW1wb3J0cyIsImxpbmVzIiwidHJpbSIsImdldElzU3RhcnRPZkRpc3RpbmN0R3JvdXAiLCJlbXB0eUxpbmVzQmV0d2VlbiIsImlzU3RhcnRPZkRpc3RpbmN0R3JvdXAiLCJnZXRBbHBoYWJldGl6ZUNvbmZpZyIsIm9wdGlvbnMiLCJhbHBoYWJldGl6ZSIsImRlZmF1bHREaXN0aW5jdEdyb3VwIiwibW9kdWxlIiwibWV0YSIsImRvY3MiLCJkZXNjcmlwdGlvbiIsInVybCIsImZpeGFibGUiLCJzY2hlbWEiLCJwcm9wZXJ0aWVzIiwicGF0aEdyb3Vwc0V4Y2x1ZGVkSW1wb3J0VHlwZXMiLCJpdGVtcyIsImFkZGl0aW9uYWxQcm9wZXJ0aWVzIiwicmVxdWlyZWQiLCJvbmVPZiIsImVuYWJsZWQiLCJyZXF1aXJlIiwiY2pzRXhwb3J0cyIsIndhcm5PblVuYXNzaWduZWRJbXBvcnRzIiwiY3JlYXRlIiwiU2V0IiwibmFtZWRHcm91cHMiLCJlcnJvciIsIlByb2dyYW0iLCJpbXBvcnRNYXAiLCJNYXAiLCJleHBvcnRNYXAiLCJnZXRCbG9ja0ltcG9ydHMiLCJzZXQiLCJnZXQiLCJnZXRCbG9ja0V4cG9ydHMiLCJtYWtlTmFtZWRPcmRlclJlcG9ydCIsIm5hbWVkSW1wb3J0cyIsImltcG9ydHMiLCJuYW1lZEltcG9ydCIsImtpbmQiLCJlbnRyeSIsIkltcG9ydERlY2xhcmF0aW9uIiwic291cmNlIiwic3BlY2lmaWVyIiwibG9jYWwiLCJUU0ltcG9ydEVxdWFsc0RlY2xhcmF0aW9uIiwiaXNFeHBvcnQiLCJnZXRUZXh0IiwiQ2FsbEV4cHJlc3Npb24iLCJibG9jayIsIlZhcmlhYmxlRGVjbGFyYXRvciIsInByb3AiLCJFeHBvcnROYW1lZERlY2xhcmF0aW9uIiwiZXhwb3J0ZWQiLCJBc3NpZ25tZW50RXhwcmVzc2lvbiIsImxlZnQiLCJyaWdodCIsIm5hbWVQYXJ0cyIsImpvaW4iLCJjbGVhciJdLCJtYXBwaW5ncyI6IkFBQUEsYTs7QUFFQSxzQztBQUNBLCtDO0FBQ0Esd0M7QUFDQTtBQUNBLDJEOztBQUVBLGdEO0FBQ0Esc0Q7QUFDQSxxQzs7QUFFQSxJQUFNQSxhQUFhO0FBQ2pCQyxTQUFPLE9BRFU7QUFFakIsWUFBUSxRQUZTO0FBR2pCQyxXQUFTLFNBSFEsRUFBbkI7OztBQU1BLElBQU1DLGdCQUFnQixDQUFDLFNBQUQsRUFBWSxVQUFaLEVBQXdCLFFBQXhCLEVBQWtDLFNBQWxDLEVBQTZDLE9BQTdDLENBQXRCOztBQUVBOztBQUVBLFNBQVNDLE9BQVQsQ0FBaUJDLEtBQWpCLEVBQXdCO0FBQ3RCLFNBQU9BLE1BQU1DLEdBQU4sQ0FBVSxVQUFDQyxDQUFELDRCQUFhQSxDQUFiLElBQWdCQyxNQUFNLENBQUNELEVBQUVDLElBQXpCLEtBQVYsRUFBNENKLE9BQTVDLEVBQVA7QUFDRDs7QUFFRCxTQUFTSyx3QkFBVCxDQUFrQ0MsVUFBbEMsRUFBOENDLElBQTlDLEVBQW9EQyxLQUFwRCxFQUEyRDtBQUN6RCxNQUFJQyxxQkFBcUJGLElBQXpCO0FBQ0EsTUFBTUcsU0FBUyxFQUFmO0FBQ0EsT0FBSyxJQUFJ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SUFBVixDQUFlLEdBQWYsQ0FBYjtBQUNBeEIsa0NBQWdCcFEsS0FBS3FCLE1BQUwsQ0FBWUEsTUFBNUIsRUFBb0NmLElBQXBDLENBQXlDO0FBQ3ZDTiw4QkFEdUM7QUFFdkN1QywyQkFBT00sSUFGZ0M7QUFHdkNpRCxpQ0FBYWpELElBSDBCO0FBSXZDcEIsMEJBQU0sUUFKaUM7QUFLdkM1QiwwQkFBTSxDQUxpQyxFQUF6Qzs7QUFPRDtBQUNGO0FBQ0Y7QUFDRixXQXhDb0IsaUNBcEl6Qjs7QUE4S0Usc0JBOUtGLHNDQThLbUI7QUFDZmlRLHNCQUFVMUksT0FBVixDQUFrQixVQUFDckcsUUFBRCxFQUFjO0FBQzlCLGtCQUFJNE0sMkJBQTJCLFFBQS9CLEVBQXlDO0FBQ3ZDRCwwQ0FBMEI3SixPQUExQixFQUFtQzlDLFFBQW5DLEVBQTZDNE0sc0JBQTdDLEVBQXFFQyxhQUFyRTtBQUNEOztBQUVELGtCQUFJVSxZQUFZbEosS0FBWixLQUFzQixRQUExQixFQUFvQztBQUNsQ2dFLHlDQUF5QnJJLFFBQXpCLEVBQW1DdU4sV0FBbkM7QUFDRDs7QUFFRDVHLG1DQUFxQjdELE9BQXJCLEVBQThCOUMsUUFBOUIsRUFBd0MxQixvQkFBeEM7QUFDRCxhQVZEOztBQVlBMlEsc0JBQVU1SSxPQUFWLENBQWtCLFVBQUNtSyxRQUFELEVBQWM7QUFDOUIsa0JBQUlqRCxZQUFZbEosS0FBWixLQUFzQixRQUExQixFQUFvQztBQUNsQ2dFLHlDQUF5Qm1JLFFBQXpCLEVBQW1DakQsV0FBbkM7QUFDQTVHLHFDQUFxQjdELE9BQXJCLEVBQThCME4sUUFBOUIsRUFBd0NsUyxXQUFXRSxPQUFuRDtBQUNEO0FBQ0YsYUFMRDs7QUFPQXVRLHNCQUFVK0IsS0FBVjtBQUNBN0Isc0JBQVU2QixLQUFWO0FBQ0QsV0FwTUg7O0FBc01ELEtBclljLG1CQUFqQiIsImZpbGUiOiJvcmRlci5qcyIsInNvdXJjZXNDb250ZW50IjpbIid1c2Ugc3RyaWN0JztcblxuaW1wb3J0IG1pbmltYXRjaCBmcm9tICdtaW5pbWF0Y2gnO1xuaW1wb3J0IGluY2x1ZGVzIGZyb20gJ2FycmF5LWluY2x1ZGVzJztcbmltcG9ydCBncm91cEJ5IGZyb20gJ29iamVjdC5ncm91cGJ5JztcbmltcG9ydCB7IGdldFNjb3BlLCBnZXRTb3VyY2VDb2RlIH0gZnJvbSAnZXNsaW50LW1vZHVsZS11dGlscy9jb250ZXh0Q29tcGF0JztcbmltcG9ydCB0cmltRW5kIGZyb20gJ3N0cmluZy5wcm90b3R5cGUudHJpbWVuZCc7XG5cbmltcG9ydCBpbXBvcnRUeXBlIGZyb20gJy4uL2NvcmUvaW1wb3J0VHlwZSc7XG5pbXBvcnQgaXNTdGF0aWNSZXF1aXJlIGZyb20gJy4uL2NvcmUvc3RhdGljUmVxdWlyZSc7XG5pbXBvcnQgZG9jc1VybCBmcm9tICcuLi9kb2NzVXJsJztcblxuY29uc3QgY2F0ZWdvcmllcyA9IHtcbiAgbmFtZWQ6ICduYW1lZCcsXG4gIGltcG9ydDogJ2ltcG9ydCcsXG4gIGV4cG9ydHM6ICdleHBvcnRzJyxcbn07XG5cbmNvbnN0IGRlZmF1bHRHcm91cHMgPSBbJ2J1aWx0aW4nLCAnZXh0ZXJuYWwnLCAncGFyZW50JywgJ3NpYmxpbmcnLCAnaW5kZXgnXTtcblxuLy8gUkVQT1JUSU5HIEFORCBGSVhJTkdcblxuZnVuY3Rpb24gcmV2ZXJzZShhcnJheSkge1xuICByZXR1cm4gYXJyYXkubWFwKCh2KSA9PiAoeyAuLi52LCByYW5rOiAtdi5yYW5rIH0pKS5yZXZlcnNlKCk7XG59XG5cbmZ1bmN0aW9uIGdldFRva2Vuc09yQ29tbWVudHNBZnRlcihzb3VyY2VDb2RlLCBub2RlLCBjb3VudCkge1xuICBsZXQgY3VycmVudE5vZGVPclRva2VuID0gbm9kZTtcbiAgY29uc3QgcmVzdWx0ID0gW107XG4gIGZvciAobGV0IGkgPSAwOyBpIDwgY291bnQ7IGkrKykge1xuICAgIGN1cnJlbnROb2RlT3JUb2tlbiA9IHNvdXJjZUNvZGUuZ2V0VG9rZW5PckNvbW1lbnRBZnRlcihjdXJyZW50Tm9kZU9yVG9rZW4pO1xuICAgIGlmIChjdXJyZW50Tm9kZU9yVG9rZW4gPT0gbnVsbCkge1xuICAgICAgYnJlYWs7XG4gICAgfVxuICAgIHJlc3VsdC5wdXNoKGN1cnJlbnROb2RlT3JUb2tlbik7XG4gIH1cbiAgcmV0dXJuIHJlc3VsdDtcbn1cblxuZnVuY3Rpb24gZ2V0VG9rZW5zT3JDb21tZW50c0JlZm9yZShzb3VyY2VDb2RlLCBub2RlLCBjb3VudCkge1xuICBsZXQgY3VycmVudE5vZGVPclRva2VuID0gbm9kZTtcbiAgY29uc3QgcmVzdWx0ID0gW107XG4gIGZvciAobGV0IGkgPSAwOyBpIDwgY291bnQ7IGkrKykge1xuICAgIGN1cnJlbnROb2RlT3JUb2tlbiA9IHNvdXJjZUNvZGUuZ2V0VG9rZW5PckNvbW1lbnRCZWZvcmUoY3VycmVudE5vZGVPclRva2VuKTtcbiAgICBpZiAoY3VycmVudE5vZGVPclRva2VuID09IG51bGwpIHtcbiAgICAgIGJyZWFrO1xuICAgIH1cbiAgICByZXN1bHQucHVzaChjdXJyZW50Tm9kZU9yVG9rZW4pO1xuICB9XG4gIHJldHVybiByZXN1bHQucmV2ZXJzZSgpO1xufVxuXG5mdW5jdGlvbiB0YWtlVG9rZW5zQWZ0ZXJXaGlsZShzb3VyY2VDb2RlLCBub2RlLCBjb25kaXRpb24pIHtcbiAgY29uc3QgdG9rZW5zID0gZ2V0VG9rZW5zT3JDb21tZW50c0FmdGVyKHNvdXJjZUNvZGUsIG5vZGUsIDEwMCk7XG4gIGNvbnN0IHJlc3VsdCA9IFtdO1xuICBmb3IgKGxldCBpID0gMDsgaSA8IHRva2Vucy5sZW5ndGg7IGkrKykge1xuICAgIGlmIChjb25kaXRpb24odG9rZW5zW2ldKSkge1xuICAgICAgcmVzdWx0LnB1c2godG9rZW5zW2ldKTtcbiAgICB9IGVsc2Uge1xuICAgICAgYnJlYWs7XG4gICAgfVxuICB9XG4gIHJldHVybiByZXN1bHQ7XG59XG5cbmZ1bmN0aW9uIHRha2VUb2tlbnNCZWZvcmVXaGlsZShzb3VyY2VDb2RlLCBub2RlLCBjb25kaXRpb24pIHtcbiAgY29uc3QgdG9rZW5zID0gZ2V0VG9rZW5zT3JDb21tZW50c0JlZm9yZShzb3VyY2VDb2RlLCBub2RlLCAxMDApO1xuICBjb25zdCByZXN1bHQgPSBbXTtcbiAgZm9yIChsZXQgaSA9IHRva2Vucy5sZW5ndGggLSAxOyBpID49IDA7IGktLSkge1xuICAgIGlmIChjb25kaXRpb24odG9rZW5zW2ldKSkge1xuICAgICAgcmVzdWx0LnB1c2godG9rZW5zW2ldKTtcbiAgICB9IGVsc2Uge1xuICAgICAgYnJlYWs7XG4gICAgfVxuICB9XG4gIHJldHVybiByZXN1bHQucmV2ZXJzZSgpO1xufVxuXG5mdW5jdGlvbiBmaW5kT3V0T2ZPcmRlcihpbXBvcnRlZCkge1xuICBpZiAoaW1wb3J0ZWQubGVuZ3RoID09PSAwKSB7XG4gICAgcmV0dXJuIFtdO1xuICB9XG4gIGxldCBtYXhTZWVuUmFua05vZGUgPSBpbXBvcnRlZFswXTtcbiAgcmV0dXJuIGltcG9ydGVkLmZpbHRlcihmdW5jdGlvbiAoaW1wb3J0ZWRNb2R1bGUpIHtcbiAgICBjb25zdCByZXMgPSBpbXBvcnRlZE1vZHVsZS5yYW5rIDwgbWF4U2VlblJhbmtOb2RlLnJhbms7XG4gICAgaWYgKG1heFNlZW5SYW5rTm9kZS5yYW5rIDwgaW1wb3J0ZWRNb2R1bGUucmFuaykge1xuICAgICAgbWF4U2VlblJhbmtOb2RlID0gaW1wb3J0ZWRNb2R1bGU7XG4gICAgfVxuICAgIHJldHVybiByZXM7XG4gIH0pO1xufVxuXG5mdW5jdGlvbiBmaW5kUm9vdE5vZGUobm9kZSkge1xuICBsZXQgcGFyZW50ID0gbm9kZTtcbiAgd2hpbGUgKHBhcmVudC5wYXJlbnQgIT0gbnVsbCAmJiBwYXJlbnQucGFyZW50LmJvZHkgPT0gbnVsbCkge1xuICAgIHBhcmVudCA9IHBhcmVudC5wYXJlbnQ7XG4gIH1cbiAgcmV0dXJuIHBhcmVudDtcbn1cblxuZnVuY3Rpb24gY29tbWVudE9uU2FtZUxpbmVBcyhub2RlKSB7XG4gIHJldHVybiAodG9rZW4pID0+ICh0b2tlbi50eXBlID09PSAnQmxvY2snIHx8ICB0b2tlbi50eXBlID09PSAnTGluZScpXG4gICAgICAmJiB0b2tlbi5sb2Muc3RhcnQubGluZSA9PT0gdG9rZW4ubG9jLmVuZC5saW5lXG4gICAgICAmJiB0b2tlbi5sb2MuZW5kLmxpbmUgPT09IG5vZGUubG9jLmVuZC5saW5lO1xufVxuXG5mdW5jdGlvbiBmaW5kRW5kT2ZMaW5lV2l0aENvbW1lbnRzKHNvdXJjZUNvZGUsIG5vZGUpIHtcbiAgY29uc3QgdG9rZW5zVG9FbmRPZkxpbmUgPSB0YWtlVG9rZW5zQWZ0ZXJXaGlsZShzb3VyY2VDb2RlLCBub2RlLCBjb21tZW50T25TYW1lTGluZUFzKG5vZGUpKTtcbiAgY29uc3QgZW5kT2ZUb2tlbnMgPSB0b2tlbnNUb0VuZE9mTGluZS5sZW5ndGggPiAwXG4gICAgPyB0b2tlbnNUb0VuZE9mTGluZVt0b2tlbnNUb0VuZE9mTGluZS5sZW5ndGggLSAxXS5yYW5nZVsxXVxuICAgIDogbm9kZS5yYW5nZVsxXTtcbiAgbGV0IHJlc3VsdCA9IGVuZE9mVG9rZW5zO1xuICBmb3IgKGxldCBpID0gZW5kT2ZUb2tlbnM7IGkgPCBzb3VyY2VDb2RlLnRleHQubGVuZ3RoOyBpKyspIHtcbiAgICBpZiAoc291cmNlQ29kZS50ZXh0W2ldID09PSAnXFxuJykge1xuICAgICAgcmVzdWx0ID0gaSArIDE7XG4gICAgICBicmVhaztcbiAgICB9XG4gICAgaWYgKHNvdXJjZUNvZGUudGV4dFtpXSAhPT0gJyAnICYmIHNvdXJjZUNvZGUudGV4dFtpXSAhPT0gJ1xcdCcgJiYgc291cmNlQ29kZS50ZXh0W2ldICE9PSAnXFxyJykge1xuICAgICAgYnJlYWs7XG4gICAgfVxuICAgIHJlc3VsdCA9IGkgKyAxO1xuICB9XG4gIHJldHVybiByZXN1bHQ7XG59XG5cbmZ1bmN0aW9uIGZpbmRTdGFydE9mTGluZVdpdGhDb21tZW50cyhzb3VyY2VDb2RlLCBub2RlKSB7XG4gIGNvbnN0IHRva2Vuc1RvRW5kT2ZMaW5lID0gdGFrZVRva2Vuc0JlZm9yZVdoaWxlKHNvdXJjZUNvZGUsIG5vZGUsIGNvbW1lbnRPblNhbWVMaW5lQXMobm9kZSkpO1xuICBjb25zdCBzdGFydE9mVG9rZW5zID0gdG9rZW5zVG9FbmRPZkxpbmUubGVuZ3RoID4gMCA/IHRva2Vuc1RvRW5kT2ZMaW5lWzBdLnJhbmdlWzBdIDogbm9kZS5yYW5nZVswXTtcbiAgbGV0IHJlc3VsdCA9IHN0YXJ0T2ZUb2tlbnM7XG4gIGZvciAobGV0IGkgPSBzdGFydE9mVG9rZW5zIC0gMTsgaSA+IDA7IGktLSkge1xuICAgIGlmIChzb3VyY2VDb2RlLnRleHRbaV0gIT09ICcgJyAmJiBzb3VyY2VDb2RlLnRleHRbaV0gIT09ICdcXHQnKSB7XG4gICAgICBicmVhaztcbiAgICB9XG4gICAgcmVzdWx0ID0gaTtcbiAgfVxuICByZXR1cm4gcmVzdWx0O1xufVxuXG5mdW5jdGlvbiBmaW5kU3BlY2lmaWVyU3RhcnQoc291cmNlQ29kZSwgbm9kZSkge1xuICBsZXQgdG9rZW47XG5cbiAgZG8ge1xuICAgIHRva2VuID0gc291cmNlQ29kZS5nZXRUb2tlbkJlZm9yZShub2RlKTtcbiAgfSB3aGlsZSAodG9rZW4udmFsdWUgIT09ICcsJyAmJiB0b2tlbi52YWx1ZSAhPT0gJ3snKTtcblxuICByZXR1cm4gdG9rZW4ucmFuZ2VbMV07XG59XG5cbmZ1bmN0aW9uIGZpbmRTcGVjaWZpZXJFbmQoc291cmNlQ29kZSwgbm9kZSkge1xuICBsZXQgdG9rZW47XG5cbiAgZG8ge1xuICAgIHRva2VuID0gc291cmNlQ29kZS5nZXRUb2tlbkFmdGVyKG5vZGUpO1xuICB9IHdoaWxlICh0b2tlbi52YWx1ZSAhPT0gJywnICYmIHRva2VuLnZhbHVlICE9PSAnfScpO1xuXG4gIHJldHVybiB0b2tlbi5yYW5nZVswXTtcbn1cblxuZnVuY3Rpb24gaXNSZXF1aXJlRXhwcmVzc2lvbihleHByKSB7XG4gIHJldHVybiBleHByICE9IG51bGxcbiAgICAmJiBleHByLnR5cGUgPT09ICdDYWxsRXhwcmVzc2lvbidcbiAgICAmJiBleHByLmNhbGxlZSAhPSBudWxsXG4gICAgJiYgZXhwci5jYWxsZWUubmFtZSA9PT0gJ3JlcXVpcmUnXG4gICAgJiYgZXhwci5hcmd1bWVudHMgIT0gbnVsbFxuICAgICYmIGV4cHIuYXJndW1lbnRzLmxlbmd0aCA9PT0gMVxuICAgICYmIGV4cHIuYXJndW1lbnRzWzBdLnR5cGUgPT09ICdMaXRlcmFsJztcbn1cblxuZnVuY3Rpb24gaXNTdXBwb3J0ZWRSZXF1aXJlTW9kdWxlKG5vZGUpIHtcbiAgaWYgKG5vZGUudHlwZSAhPT0gJ1ZhcmlhYmxlRGVjbGFyYXRpb24nKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG4gIGlmIChub2RlLmRlY2xhcmF0aW9ucy5sZW5ndGggIT09IDEpIHtcbiAgICByZXR1cm4gZmFsc2U7XG4gIH1cbiAgY29uc3QgZGVjbCA9IG5vZGUuZGVjbGFyYXRpb25zWzBdO1xuICBjb25zdCBpc1BsYWluUmVxdWlyZSA9IGRlY2wuaWRcbiAgICAmJiAoZGVjbC5pZC50eXBlID09PSAnSWRlbnRpZmllcicgfHwgZGVjbC5pZC50eXBlID09PSAnT2JqZWN0UGF0dGVybicpXG4gICAgJiYgaXNSZXF1aXJlRXhwcmVzc2lvbihkZWNsLmluaXQpO1xuICBjb25zdCBpc1JlcXVpcmVXaXRoTWVtYmVyRXhwcmVzc2lvbiA9IGRlY2wuaWRcbiAgICAmJiAoZGVjbC5pZC50eXBlID09PSAnSWRlbnRpZmllcicgfHwgZGVjbC5pZC50eXBlID09PSAnT2JqZWN0UGF0dGVybicpXG4gICAgJiYgZGVjbC5pbml0ICE9IG51bGxcbiAgICAmJiBkZWNsLmluaXQudHlwZSA9PT0gJ0NhbGxFeHByZXNzaW9uJ1xuICAgICYmIGRlY2wuaW5pdC5jYWxsZWUgIT0gbnVsbFxuICAgICYmIGRlY2wuaW5pdC5jYWxsZWUudHlwZSA9PT0gJ01lbWJlckV4cHJlc3Npb24nXG4gICAgJiYgaXNSZXF1aXJlRXhwcmVzc2lvbihkZWNsLmluaXQuY2FsbGVlLm9iamVjdCk7XG4gIHJldHVybiBpc1BsYWluUmVxdWlyZSB8fCBpc1JlcXVpcmVXaXRoTWVtYmVyRXhwcmVzc2lvbjtcbn1cblxuZnVuY3Rpb24gaXNQbGFpbkltcG9ydE1vZHVsZShub2RlKSB7XG4gIHJldHVybiBub2RlLnR5cGUgPT09ICdJbXBvcnREZWNsYXJhdGlvbicgJiYgbm9kZS5zcGVjaWZpZXJzICE9IG51bGwgJiYgbm9kZS5zcGVjaWZpZXJzLmxlbmd0aCA+IDA7XG59XG5cbmZ1bmN0aW9uIGlzUGxhaW5JbXBvcnRFcXVhbHMobm9kZSkge1xuICByZXR1cm4gbm9kZS50eXBlID09PSAnVFNJbXBvcnRFcXVhbHNEZWNsYXJhdGlvbicgJiYgbm9kZS5tb2R1bGVSZWZlcmVuY2UuZXhwcmVzc2lvbjtcbn1cblxuZnVuY3Rpb24gaXNDSlNFeHBvcnRzKGNvbnRleHQsIG5vZGUpIHtcbiAgaWYgKFxuICAgIG5vZGUudHlwZSA9PT0gJ01lbWJlckV4cHJlc3Npb24nXG4gICAgJiYgbm9kZS5vYmplY3QudHlwZSA9PT0gJ0lkZW50aWZpZXInXG4gICAgJiYgbm9kZS5wcm9wZXJ0eS50eXBlID09PSAnSWRlbnRpZmllcidcbiAgICAmJiBub2RlLm9iamVjdC5uYW1lID09PSAnbW9kdWxlJ1xuICAgICYmIG5vZGUucHJvcGVydHkubmFtZSA9PT0gJ2V4cG9ydHMnXG4gICkge1xuICAgIHJldHVybiBnZXRTY29wZShjb250ZXh0LCBub2RlKS52YXJpYWJsZXMuZmluZEluZGV4KCh2YXJpYWJsZSkgPT4gdmFyaWFibGUubmFtZSA9PT0gJ21vZHVsZScpID09PSAtMTtcbiAgfVxuICBpZiAoXG4gICAgbm9kZS50eXBlID09PSAnSWRlbnRpZmllcidcbiAgICAmJiBub2RlLm5hbWUgPT09ICdleHBvcnRzJ1xuICApIHtcbiAgICByZXR1cm4gZ2V0U2NvcGUoY29udGV4dCwgbm9kZSkudmFyaWFibGVzLmZpbmRJbmRleCgodmFyaWFibGUpID0+IHZhcmlhYmxlLm5hbWUgPT09ICdleHBvcnRzJykgPT09IC0xO1xuICB9XG59XG5cbmZ1bmN0aW9uIGdldE5hbWVkQ0pTRXhwb3J0cyhjb250ZXh0LCBub2RlKSB7XG4gIGlmIChub2RlLnR5cGUgIT09ICdNZW1iZXJFeHByZXNzaW9uJykge1xuICAgIHJldHVybjtcbiAgfVxuICBjb25zdCByZXN1bHQgPSBbXTtcbiAgbGV0IHJvb3QgPSBub2RlO1xuICBsZXQgcGFyZW50ID0gbnVsbDtcbiAgd2hpbGUgKHJvb3QudHlwZSA9PT0gJ01lbWJlckV4cHJlc3Npb24nKSB7XG4gICAgaWYgKHJvb3QucHJvcGVydHkudHlwZSAhPT0gJ0lkZW50aWZpZXInKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuICAgIHJlc3VsdC51bnNoaWZ0KHJvb3QucHJvcGVydHkubmFtZSk7XG4gICAgcGFyZW50ID0gcm9vdDtcbiAgICByb290ID0gcm9vdC5vYmplY3Q7XG4gIH1cblxuICBpZiAoaXNDSlNFeHBvcnRzKGNvbnRleHQsIHJvb3QpKSB7XG4gICAgcmV0dXJuIHJlc3VsdDtcbiAgfVxuXG4gIGlmIChpc0NKU0V4cG9ydHMoY29udGV4dCwgcGFyZW50KSkge1xuICAgIHJldHVybiByZXN1bHQuc2xpY2UoMSk7XG4gIH1cbn1cblxuZnVuY3Rpb24gY2FuQ3Jvc3NOb2RlV2hpbGVSZW9yZGVyKG5vZGUpIHtcbiAgcmV0dXJuIGlzU3VwcG9ydGVkUmVxdWlyZU1vZHVsZShub2RlKSB8fCBpc1BsYWluSW1wb3J0TW9kdWxlKG5vZGUpIHx8IGlzUGxhaW5JbXBvcnRFcXVhbHMobm9kZSk7XG59XG5cbmZ1bmN0aW9uIGNhblJlb3JkZXJJdGVtcyhmaXJzdE5vZGUsIHNlY29uZE5vZGUpIHtcbiAgY29uc3QgcGFyZW50ID0gZmlyc3ROb2RlLnBhcmVudDtcbiAgY29uc3QgW2ZpcnN0SW5kZXgsIHNlY29uZEluZGV4XSA9IFtcbiAgICBwYXJlbnQuYm9keS5pbmRleE9mKGZpcnN0Tm9kZSksXG4gICAgcGFyZW50LmJvZHkuaW5kZXhPZihzZWNvbmROb2RlKSxcbiAgXS5zb3J0KCk7XG4gIGNvbnN0IG5vZGVzQmV0d2VlbiA9IHBhcmVudC5ib2R5LnNsaWNlKGZpcnN0SW5kZXgsIHNlY29uZEluZGV4ICsgMSk7XG4gIGZvciAoY29uc3Qgbm9kZUJldHdlZW4gb2Ygbm9kZXNCZXR3ZWVuKSB7XG4gICAgaWYgKCFjYW5Dcm9zc05vZGVXaGlsZVJlb3JkZXIobm9kZUJldHdlZW4pKSB7XG4gICAgICByZXR1cm4gZmFsc2U7XG4gICAgfVxuICB9XG4gIHJldHVybiB0cnVlO1xufVxuXG5mdW5jdGlvbiBtYWtlSW1wb3J0RGVzY3JpcHRpb24obm9kZSkge1xuICBpZiAobm9kZS50eXBlID09PSAnZXhwb3J0Jykge1xuICAgIGlmIChub2RlLm5vZGUuZXhwb3J0S2luZCA9PT0gJ3R5cGUnKSB7XG4gICAgICByZXR1cm4gJ3R5cGUgZXhwb3J0JztcbiAgICB9XG4gICAgcmV0dXJuICdleHBvcnQnO1xuICB9XG4gIGlmIChub2RlLm5vZGUuaW1wb3J0S2luZCA9PT0gJ3R5cGUnKSB7XG4gICAgcmV0dXJuICd0eXBlIGltcG9ydCc7XG4gIH1cbiAgaWYgKG5vZGUubm9kZS5pbXBvcnRLaW5kID09PSAndHlwZW9mJykge1xuICAgIHJldHVybiAndHlwZW9mIGltcG9ydCc7XG4gIH1cbiAgcmV0dXJuICdpbXBvcnQnO1xufVxuXG5mdW5jdGlvbiBmaXhPdXRPZk9yZGVyKGNvbnRleHQsIGZpcnN0Tm9kZSwgc2Vjb25kTm9kZSwgb3JkZXIsIGNhdGVnb3J5KSB7XG4gIGNvbnN0IGlzTmFtZWQgPSBjYXRlZ29yeSA9PT0gY2F0ZWdvcmllcy5uYW1lZDtcbiAgY29uc3QgaXNFeHBvcnRzID0gY2F0ZWdvcnkgPT09IGNhdGVnb3JpZXMuZXhwb3J0cztcbiAgY29uc3Qgc291cmNlQ29kZSA9IGdldFNvdXJjZUNvZGUoY29udGV4dCk7XG5cbiAgY29uc3Qge1xuICAgIGZpcnN0Um9vdCxcbiAgICBzZWNvbmRSb290LFxuICB9ID0gaXNOYW1lZCA/IHtcbiAgICBmaXJzdFJvb3Q6IGZpcnN0Tm9kZS5ub2RlLFxuICAgIHNlY29uZFJvb3Q6IHNlY29uZE5vZGUubm9kZSxcbiAgfSA6IHtcbiAgICBmaXJzdFJvb3Q6IGZpbmRSb290Tm9kZShmaXJzdE5vZGUubm9kZSksXG4gICAgc2Vjb25kUm9vdDogZmluZFJvb3ROb2RlKHNlY29uZE5vZGUubm9kZSksXG4gIH07XG5cbiAgY29uc3Qge1xuICAgIGZpcnN0Um9vdFN0YXJ0LFxuICAgIGZpcnN0Um9vdEVuZCxcbiAgICBzZWNvbmRSb290U3RhcnQsXG4gICAgc2Vjb25kUm9vdEVuZCxcbiAgfSA9IGlzTmFtZWQgPyB7XG4gICAgZmlyc3RSb290U3RhcnQ6IGZpbmRTcGVjaWZpZXJTdGFydChzb3VyY2VDb2RlLCBmaXJzdFJvb3QpLFxuICAgIGZpcnN0Um9vdEVuZDogZmluZFNwZWNpZmllckVuZChzb3VyY2VDb2RlLCBmaXJzdFJvb3QpLFxuICAgIHNlY29uZFJvb3RTdGFydDogZmluZFNwZWNpZmllclN0YXJ0KHNvdXJjZUNvZGUsIHNlY29uZFJvb3QpLFxuICAgIHNlY29uZFJvb3RFbmQ6IGZpbmRTcGVjaWZpZXJFbmQoc291cmNlQ29kZSwgc2Vjb25kUm9vdCksXG4gIH0gOiB7XG4gICAgZmlyc3RSb290U3RhcnQ6IGZpbmRTdGFydE9mTGluZVdpdGhDb21tZW50cyhzb3VyY2VDb2RlLCBmaXJzdFJvb3QpLFxuICAgIGZpcnN0Um9vdEVuZDogZmluZEVuZE9mTGluZVdpdGhDb21tZW50cyhzb3VyY2VDb2RlLCBmaXJzdFJvb3QpLFxuICAgIHNlY29uZFJvb3RTdGFydDogZmluZFN0YXJ0T2ZMaW5lV2l0aENvbW1lbnRzKHNvdXJjZUNvZGUsIHNlY29uZFJvb3QpLFxuICAgIHNlY29uZFJvb3RFbmQ6IGZpbmRFbmRPZkxpbmVXaXRoQ29tbWVudHMoc291cmNlQ29kZSwgc2Vjb25kUm9vdCksXG4gIH07XG5cbiAgaWYgKGZpcnN0Tm9kZS5kaXNwbGF5TmFtZSA9PT0gc2Vjb25kTm9kZS5kaXNwbGF5TmFtZSkge1xuICAgIGlmIChmaXJzdE5vZGUuYWxpYXMpIHtcbiAgICAgIGZpcnN0Tm9kZS5kaXNwbGF5TmFtZSA9IGAke2ZpcnN0Tm9kZS5kaXNwbGF5TmFtZX0gYXMgJHtmaXJzdE5vZGUuYWxpYXN9YDtcbiAgICB9XG4gICAgaWYgKHNlY29uZE5vZGUuYWxpYXMpIHtcbiAgICAgIHNlY29uZE5vZGUuZGlzcGxheU5hbWUgPSBgJHtzZWNvbmROb2RlLmRpc3BsYXlOYW1lfSBhcyAke3NlY29uZE5vZGUuYWxpYXN9YDtcbiAgICB9XG4gIH1cblxuICBjb25zdCBmaXJzdEltcG9ydCA9IGAke21ha2VJbXBvcnREZXNjcmlwdGlvbihmaXJzdE5vZGUpfSBvZiBcXGAke2ZpcnN0Tm9kZS5kaXNwbGF5TmFtZX1cXGBgO1xuICBjb25zdCBzZWNvbmRJbXBvcnQgPSBgXFxgJHtzZWNvbmROb2RlLmRpc3BsYXlOYW1lfVxcYCAke21ha2VJbXBvcnREZXNjcmlwdGlvbihzZWNvbmROb2RlKX1gO1xuICBjb25zdCBtZXNzYWdlID0gYCR7c2Vjb25kSW1wb3J0fSBzaG91bGQgb2NjdXIgJHtvcmRlcn0gJHtmaXJzdEltcG9ydH1gO1xuXG4gIGlmIChpc05hbWVkKSB7XG4gICAgY29uc3QgZmlyc3RDb2RlID0gc291cmNlQ29kZS50ZXh0LnNsaWNlKGZpcnN0Um9vdFN0YXJ0LCBmaXJzdFJvb3QucmFuZ2VbMV0pO1xuICAgIGNvbnN0IGZpcnN0VHJpdmlhID0gc291cmNlQ29kZS50ZXh0LnNsaWNlKGZpcnN0Um9vdC5yYW5nZVsxXSwgZmlyc3RSb290RW5kKTtcbiAgICBjb25zdCBzZWNvbmRDb2RlID0gc291cmNlQ29kZS50ZXh0LnNsaWNlKHNlY29uZFJvb3RTdGFydCwgc2Vjb25kUm9vdC5yYW5nZVsxXSk7XG4gICAgY29uc3Qgc2Vjb25kVHJpdmlhID0gc291cmNlQ29kZS50ZXh0LnNsaWNlKHNlY29uZFJvb3QucmFuZ2VbMV0sIHNlY29uZFJvb3RFbmQpO1xuXG4gICAgaWYgKG9yZGVyID09PSAnYmVmb3JlJykge1xuICAgICAgY29uc3QgdHJpbW1lZFRyaXZpYSA9IHRyaW1FbmQoc2Vjb25kVHJpdmlhKTtcbiAgICAgIGNvbnN0IGdhcENvZGUgPSBzb3VyY2VDb2RlLnRleHQuc2xpY2UoZmlyc3RSb290RW5kLCBzZWNvbmRSb290U3RhcnQgLSAxKTtcbiAgICAgIGNvbnN0IHdoaXRlc3BhY2VzID0gc2Vjb25kVHJpdmlhLnNsaWNlKHRyaW1tZWRUcml2aWEubGVuZ3RoKTtcbiAgICAgIGNvbnRleHQucmVwb3J0KHtcbiAgICAgICAgbm9kZTogc2Vjb25kTm9kZS5ub2RlLFxuICAgICAgICBtZXNzYWdlLFxuICAgICAgICBmaXg6IChmaXhlcikgPT4gZml4ZXIucmVwbGFjZVRleHRSYW5nZShcbiAgICAgICAgICBbZmlyc3RSb290U3RhcnQsIHNlY29uZFJvb3RFbmRdLFxuICAgICAgICAgIGAke3NlY29uZENvZGV9LCR7dHJpbW1lZFRyaXZpYX0ke2ZpcnN0Q29kZX0ke2ZpcnN0VHJpdmlhfSR7Z2FwQ29kZX0ke3doaXRlc3BhY2VzfWAsXG4gICAgICAgICksXG4gICAgICB9KTtcbiAgICB9IGVsc2UgaWYgKG9yZGVyID09PSAnYWZ0ZXInKSB7XG4gICAgICBjb25zdCB0cmltbWVkVHJpdmlhID0gdHJpbUVuZChmaXJzdFRyaXZpYSk7XG4gICAgICBjb25zdCBnYXBDb2RlID0gc291cmNlQ29kZS50ZXh0LnNsaWNlKHNlY29uZFJvb3RFbmQgKyAxLCBmaXJzdFJvb3RTdGFydCk7XG4gICAgICBjb25zdCB3aGl0ZXNwYWNlcyA9IGZpcnN0VHJpdmlhLnNsaWNlKHRyaW1tZWRUcml2aWEubGVuZ3RoKTtcbiAgICAgIGNvbnRleHQucmVwb3J0KHtcbiAgICAgICAgbm9kZTogc2Vjb25kTm9kZS5ub2RlLFxuICAgICAgICBtZXNzYWdlLFxuICAgICAgICBmaXg6IChmaXhlcykgPT4gZml4ZXMucmVwbGFjZVRleHRSYW5nZShcbiAgICAgICAgICBbc2Vjb25kUm9vdFN0YXJ0LCBmaXJzdFJvb3RFbmRdLFxuICAgICAgICAgIGAke2dhcENvZGV9JHtmaXJzdENvZGV9LCR7dHJpbW1lZFRyaXZpYX0ke3NlY29uZENvZGV9JHt3aGl0ZXNwYWNlc31gLFxuICAgICAgICApLFxuICAgICAgfSk7XG4gICAgfVxuICB9IGVsc2Uge1xuICAgIGNvbnN0IGNhbkZpeCA9IGlzRXhwb3J0cyB8fCBjYW5SZW9yZGVySXRlbXMoZmlyc3RSb290LCBzZWNvbmRSb290KTtcbiAgICBsZXQgbmV3Q29kZSA9IHNvdXJjZUNvZGUudGV4dC5zdWJzdHJpbmcoc2Vjb25kUm9vdFN0YXJ0LCBzZWNvbmRSb290RW5kKTtcblxuICAgIGlmIChuZXdDb2RlW25ld0NvZGUubGVuZ3RoIC0gMV0gIT09ICdcXG4nKSB7XG4gICAgICBuZXdDb2RlID0gYCR7bmV3Q29kZX1cXG5gO1xuICAgIH1cblxuICAgIGlmIChvcmRlciA9PT0gJ2JlZm9yZScpIHtcbiAgICAgIGNvbnRleHQucmVwb3J0KHtcbiAgICAgICAgbm9kZTogc2Vjb25kTm9kZS5ub2RlLFxuICAgICAgICBtZXNzYWdlLFxuICAgICAgICBmaXg6IGNhbkZpeCAmJiAoKGZpeGVyKSA9PiBmaXhlci5yZXBsYWNlVGV4dFJhbmdlKFxuICAgICAgICAgIFtmaXJzdFJvb3RTdGFydCwgc2Vjb25kUm9vdEVuZF0sXG4gICAgICAgICAgbmV3Q29kZSArIHNvdXJjZUNvZGUudGV4dC5zdWJzdHJpbmcoZmlyc3RSb290U3RhcnQsIHNlY29uZFJvb3RTdGFydCksXG4gICAgICAgICkpLFxuICAgICAgfSk7XG4gICAgfSBlbHNlIGlmIChvcmRlciA9PT0gJ2FmdGVyJykge1xuICAgICAgY29udGV4dC5yZXBvcnQoe1xuICAgICAgICBub2RlOiBzZWNvbmROb2RlLm5vZGUsXG4gICAgICAgIG1lc3NhZ2UsXG4gICAgICAgIGZpeDogY2FuRml4ICYmICgoZml4ZXIpID0+IGZpeGVyLnJlcGxhY2VUZXh0UmFuZ2UoXG4gICAgICAgICAgW3NlY29uZFJvb3RTdGFydCwgZmlyc3RSb290RW5kXSxcbiAgICAgICAgICBzb3VyY2VDb2RlLnRleHQuc3Vic3RyaW5nKHNlY29uZFJvb3RFbmQsIGZpcnN0Um9vdEVuZCkgKyBuZXdDb2RlLFxuICAgICAgICApKSxcbiAgICAgIH0pO1xuICAgIH1cbiAgfVxufVxuXG5mdW5jdGlvbiByZXBvcnRPdXRPZk9yZGVyKGNvbnRleHQsIGltcG9ydGVkLCBvdXRPZk9yZGVyLCBvcmRlciwgY2F0ZWdvcnkpIHtcbiAgb3V0T2ZPcmRlci5mb3JFYWNoKGZ1bmN0aW9uIChpbXApIHtcbiAgICBjb25zdCBmb3VuZCA9IGltcG9ydGVkLmZpbmQoZnVuY3Rpb24gaGFzSGlnaGVyUmFuayhpbXBvcnRlZEl0ZW0pIHtcbiAgICAgIHJldHVybiBpbXBvcnRlZEl0ZW0ucmFuayA+IGltcC5yYW5rO1xuICAgIH0pO1xuICAgIGZpeE91dE9mT3JkZXIoY29udGV4dCwgZm91bmQsIGltcCwgb3JkZXIsIGNhdGVnb3J5KTtcbiAgfSk7XG59XG5cbmZ1bmN0aW9uIG1ha2VPdXRPZk9yZGVyUmVwb3J0KGNvbnRleHQsIGltcG9ydGVkLCBjYXRlZ29yeSkge1xuICBjb25zdCBvdXRPZk9yZGVyID0gZmluZE91dE9mT3JkZXIoaW1wb3J0ZWQpO1xuICBpZiAoIW91dE9mT3JkZXIubGVuZ3RoKSB7XG4gICAgcmV0dXJuO1xuICB9XG5cbiAgLy8gVGhlcmUgYXJlIHRoaW5ncyB0byByZXBvcnQuIFRyeSB0byBtaW5pbWl6ZSB0aGUgbnVtYmVyIG9mIHJlcG9ydGVkIGVycm9ycy5cbiAgY29uc3QgcmV2ZXJzZWRJbXBvcnRlZCA9IHJldmVyc2UoaW1wb3J0ZWQpO1xuICBjb25zdCByZXZlcnNlZE9yZGVyID0gZmluZE91dE9mT3JkZXIocmV2ZXJzZWRJbXBvcnRlZCk7XG4gIGlmIChyZXZlcnNlZE9yZGVyLmxlbmd0aCA8IG91dE9mT3JkZXIubGVuZ3RoKSB7XG4gICAgcmVwb3J0T3V0T2ZPcmRlcihjb250ZXh0LCByZXZlcnNlZEltcG9ydGVkLCByZXZlcnNlZE9yZGVyLCAnYWZ0ZXInLCBjYXRlZ29yeSk7XG4gICAgcmV0dXJuO1xuICB9XG4gIHJlcG9ydE91dE9mT3JkZXIoY29udGV4dCwgaW1wb3J0ZWQsIG91dE9mT3JkZXIsICdiZWZvcmUnLCBjYXRlZ29yeSk7XG59XG5cbmNvbnN0IGNvbXBhcmVTdHJpbmcgPSAoYSwgYikgPT4ge1xuICBpZiAoYSA8IGIpIHtcbiAgICByZXR1cm4gLTE7XG4gIH1cbiAgaWYgKGEgPiBiKSB7XG4gICAgcmV0dXJuIDE7XG4gIH1cbiAgcmV0dXJuIDA7XG59O1xuXG4vKiogU29tZSBwYXJzZXJzIChsYW5ndWFnZXMgd2l0aG91dCB0eXBlcykgZG9uJ3QgcHJvdmlkZSBJbXBvcnRLaW5kICovXG5jb25zdCBERUFGVUxUX0lNUE9SVF9LSU5EID0gJ3ZhbHVlJztcbmNvbnN0IGdldE5vcm1hbGl6ZWRWYWx1ZSA9IChub2RlLCB0b0xvd2VyQ2FzZSkgPT4ge1xuICBjb25zdCB2YWx1ZSA9IG5vZGUudmFsdWU7XG4gIHJldHVybiB0b0xvd2VyQ2FzZSA/IFN0cmluZyh2YWx1ZSkudG9Mb3dlckNhc2UoKSA6IHZhbHVlO1xufTtcblxuZnVuY3Rpb24gZ2V0U29ydGVyKGFscGhhYmV0aXplT3B0aW9ucykge1xuICBjb25zdCBtdWx0aXBsaWVyID0gYWxwaGFiZXRpemVPcHRpb25zLm9yZGVyID09PSAnYXNjJyA/IDEgOiAtMTtcbiAgY29uc3Qgb3JkZXJJbXBvcnRLaW5kID0gYWxwaGFiZXRpemVPcHRpb25zLm9yZGVySW1wb3J0S2luZDtcbiAgY29uc3QgbXVsdGlwbGllckltcG9ydEtpbmQgPSBvcmRlckltcG9ydEtpbmQgIT09ICdpZ25vcmUnXG4gICAgJiYgKGFscGhhYmV0aXplT3B0aW9ucy5vcmRlckltcG9ydEtpbmQgPT09ICdhc2MnID8gMSA6IC0xKTtcblxuICByZXR1cm4gZnVuY3Rpb24gaW1wb3J0c1NvcnRlcihub2RlQSwgbm9kZUIpIHtcbiAgICBjb25zdCBpbXBvcnRBID0gZ2V0Tm9ybWFsaXplZFZhbHVlKG5vZGVBLCBhbHBoYWJldGl6ZU9wdGlvbnMuY2FzZUluc2Vuc2l0aXZlKTtcbiAgICBjb25zdCBpbXBvcnRCID0gZ2V0Tm9ybWFsaXplZFZhbHVlKG5vZGVCLCBhbHBoYWJldGl6ZU9wdGlvbnMuY2FzZUluc2Vuc2l0aXZlKTtcbiAgICBsZXQgcmVzdWx0ID0gMDtcblxuICAgIGlmICghaW5jbHVkZXMoaW1wb3J0QSwgJy8nKSAmJiAhaW5jbHVkZXMoaW1wb3J0QiwgJy8nKSkge1xuICAgICAgcmVzdWx0ID0gY29tcGFyZVN0cmluZyhpbXBvcnRBLCBpbXBvcnRCKTtcbiAgICB9IGVsc2Uge1xuICAgICAgY29uc3QgQSA9IGltcG9ydEEuc3BsaXQoJy8nKTtcbiAgICAgIGNvbnN0IEIgPSBpbXBvcnRCLnNwbGl0KCcvJyk7XG4gICAgICBjb25zdCBhID0gQS5sZW5ndGg7XG4gICAgICBjb25zdCBiID0gQi5sZW5ndGg7XG5cbiAgICAgIGZvciAobGV0IGkgPSAwOyBpIDwgTWF0aC5taW4oYSwgYik7IGkrKykge1xuICAgICAgICAvLyBTa2lwIGNvbXBhcmluZyB0aGUgZmlyc3QgcGF0aCBzZWdtZW50LCBpZiB0aGV5IGFyZSByZWxhdGl2ZSBzZWdtZW50cyBmb3IgYm90aCBpbXBvcnRzXG4gICAgICAgIGlmIChpID09PSAwICYmICgoQVtpXSA9PT0gJy4nIHx8IEFbaV0gPT09ICcuLicpICYmIChCW2ldID09PSAnLicgfHwgQltpXSA9PT0gJy4uJykpKSB7XG4gICAgICAgICAgLy8gSWYgb25lIGlzIHNpYmxpbmcgYW5kIHRoZSBvdGhlciBwYXJlbnQgaW1wb3J0LCBubyBuZWVkIHRvIGNvbXBhcmUgYXQgYWxsLCBzaW5jZSB0aGUgcGF0aHMgYmVsb25nIGluIGRpZmZlcmVudCBncm91cHNcbiAgICAgICAgICBpZiAoQVtpXSAhPT0gQltpXSkgeyBicmVhazsgfVxuICAgICAgICAgIGNvbnRpbnVlO1xuICAgICAgICB9XG4gICAgICAgIHJlc3VsdCA9IGNvbXBhcmVTdHJpbmcoQVtpXSwgQltpXSk7XG4gICAgICAgIGlmIChyZXN1bHQpIHsgYnJlYWs7IH1cbiAgICAgIH1cblxuICAgICAgaWYgKCFyZXN1bHQgJiYgYSAhPT0gYikge1xuICAgICAgICByZXN1bHQgPSBhIDwgYiA/IC0xIDogMTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICByZXN1bHQgPSByZXN1bHQgKiBtdWx0aXBsaWVyO1xuXG4gICAgLy8gSW4gY2FzZSB0aGUgcGF0aHMgYXJlIGVxdWFsIChyZXN1bHQgPT09IDApLCBzb3J0IHRoZW0gYnkgaW1wb3J0S2luZFxuICAgIGlmICghcmVzdWx0ICYmIG11bHRpcGxpZXJJbXBvcnRLaW5kKSB7XG4gICAgICByZXN1bHQgPSBtdWx0aXBsaWVySW1wb3J0S2luZCAqIGNvbXBhcmVTdHJpbmcoXG4gICAgICAgIG5vZGVBLm5vZGUuaW1wb3J0S2luZCB8fCBERUFGVUxUX0lNUE9SVF9LSU5ELFxuICAgICAgICBub2RlQi5ub2RlLmltcG9ydEtpbmQgfHwgREVBRlVMVF9JTVBPUlRfS0lORCxcbiAgICAgICk7XG4gICAgfVxuXG4gICAgcmV0dXJuIHJlc3VsdDtcbiAgfTtcbn1cblxuZnVuY3Rpb24gbXV0YXRlUmFua3NUb0FscGhhYmV0aXplKGltcG9ydGVkLCBhbHBoYWJldGl6ZU9wdGlvbnMpIHtcbiAgY29uc3QgZ3JvdXBlZEJ5UmFua3MgPSBncm91cEJ5KGltcG9ydGVkLCAoaXRlbSkgPT4gaXRlbS5yYW5rKTtcblxuICBjb25zdCBzb3J0ZXJGbiA9IGdldFNvcnRlcihhbHBoYWJldGl6ZU9wdGlvbnMpO1xuXG4gIC8vIHNvcnQgZ3JvdXAga2V5cyBzbyB0aGF0IHRoZXkgY2FuIGJlIGl0ZXJhdGVkIG9uIGluIG9yZGVyXG4gIGNvbnN0IGdyb3VwUmFua3MgPSBPYmplY3Qua2V5cyhncm91cGVkQnlSYW5rcykuc29ydChmdW5jdGlvbiAoYSwgYikge1xuICAgIHJldHVybiBhIC0gYjtcbiAgfSk7XG5cbiAgLy8gc29ydCBpbXBvcnRzIGxvY2FsbHkgd2l0aGluIHRoZWlyIGdyb3VwXG4gIGdyb3VwUmFua3MuZm9yRWFjaChmdW5jdGlvbiAoZ3JvdXBSYW5rKSB7XG4gICAgZ3JvdXBlZEJ5UmFua3NbZ3JvdXBSYW5rXS5zb3J0KHNvcnRlckZuKTtcbiAgfSk7XG5cbiAgLy8gYXNzaWduIGdsb2JhbGx5IHVuaXF1ZSByYW5rIHRvIGVhY2ggaW1wb3J0XG4gIGxldCBuZXdSYW5rID0gMDtcbiAgY29uc3QgYWxwaGFiZXRpemVkUmFua3MgPSBncm91cFJhbmtzLnJlZHVjZShmdW5jdGlvbiAoYWNjLCBncm91cFJhbmspIHtcbiAgICBncm91cGVkQnlSYW5rc1tncm91cFJhbmtdLmZvckVhY2goZnVuY3Rpb24gKGltcG9ydGVkSXRlbSkge1xuICAgICAgYWNjW2Ake2ltcG9ydGVkSXRlbS52YWx1ZX18JHtpbXBvcnRlZEl0ZW0ubm9kZS5pbXBvcnRLaW5kfWBdID0gcGFyc2VJbnQoZ3JvdXBSYW5rLCAxMCkgKyBuZXdSYW5rO1xuICAgICAgbmV3UmFuayArPSAxO1xuICAgIH0pO1xuICAgIHJldHVybiBhY2M7XG4gIH0sIHt9KTtcblxuICAvLyBtdXRhdGUgdGhlIG9yaWdpbmFsIGdyb3VwLXJhbmsgd2l0aCBhbHBoYWJldGl6ZWQtcmFua1xuICBpbXBvcnRlZC5mb3JFYWNoKGZ1bmN0aW9uIChpbXBvcnRlZEl0ZW0pIHtcbiAgICBpbXBvcnRlZEl0ZW0ucmFuayA9IGFscGhhYmV0aXplZFJhbmtzW2Ake2ltcG9ydGVkSXRlbS52YWx1ZX18JHtpbXBvcnRlZEl0ZW0ubm9kZS5pbXBvcnRLaW5kfWBdO1xuICB9KTtcbn1cblxuLy8gREVURUNUSU5HXG5cbmZ1bmN0aW9uIGNvbXB1dGVQYXRoUmFuayhyYW5rcywgcGF0aEdyb3VwcywgcGF0aCwgbWF4UG9zaXRpb24pIHtcbiAgZm9yIChsZXQgaSA9IDAsIGwgPSBwYXRoR3JvdXBzLmxlbmd0aDsgaSA8IGw7IGkrKykge1xuICAgIGNvbnN0IHsgcGF0dGVybiwgcGF0dGVybk9wdGlvbnMsIGdyb3VwLCBwb3NpdGlvbiA9IDEgfSA9IHBhdGhHcm91cHNbaV07XG4gICAgaWYgKG1pbmltYXRjaChwYXRoLCBwYXR0ZXJuLCBwYXR0ZXJuT3B0aW9ucyB8fCB7IG5vY29tbWVudDogdHJ1ZSB9KSkge1xuICAgICAgcmV0dXJuIHJhbmtzW2dyb3VwXSArIHBvc2l0aW9uIC8gbWF4UG9zaXRpb247XG4gICAgfVxuICB9XG59XG5cbmZ1bmN0aW9uIGNvbXB1dGVSYW5rKGNvbnRleHQsIHJhbmtzLCBpbXBvcnRFbnRyeSwgZXhjbHVkZWRJbXBvcnRUeXBlcykge1xuICBsZXQgaW1wVHlwZTtcbiAgbGV0IHJhbms7XG4gIGlmIChpbXBvcnRFbnRyeS50eXBlID09PSAnaW1wb3J0Om9iamVjdCcpIHtcbiAgICBpbXBUeXBlID0gJ29iamVjdCc7XG4gIH0gZWxzZSBpZiAoaW1wb3J0RW50cnkubm9kZS5pbXBvcnRLaW5kID09PSAndHlwZScgJiYgcmFua3Mub21pdHRlZFR5cGVzLmluZGV4T2YoJ3R5cGUnKSA9PT0gLTEpIHtcbiAgICBpbXBUeXBlID0gJ3R5cGUnO1xuICB9IGVsc2Uge1xuICAgIGltcFR5cGUgPSBpbXBvcnRUeXBlKGltcG9ydEVudHJ5LnZhbHVlLCBjb250ZXh0KTtcbiAgfVxuICBpZiAoIWV4Y2x1ZGVkSW1wb3J0VHlwZXMuaGFzKGltcFR5cGUpKSB7XG4gICAgcmFuayA9IGNvbXB1dGVQYXRoUmFuayhyYW5rcy5ncm91cHMsIHJhbmtzLnBhdGhHcm91cHMsIGltcG9ydEVudHJ5LnZhbHVlLCByYW5rcy5tYXhQb3NpdGlvbik7XG4gIH1cbiAgaWYgKHR5cGVvZiByYW5rID09PSAndW5kZWZpbmVkJykge1xuICAgIHJhbmsgPSByYW5rcy5ncm91cHNbaW1wVHlwZV07XG4gIH1cbiAgaWYgKGltcG9ydEVudHJ5LnR5cGUgIT09ICdpbXBvcnQnICYmICFpbXBvcnRFbnRyeS50eXBlLnN0YXJ0c1dpdGgoJ2ltcG9ydDonKSkge1xuICAgIHJhbmsgKz0gMTAwO1xuICB9XG5cbiAgcmV0dXJuIHJhbms7XG59XG5cbmZ1bmN0aW9uIHJlZ2lzdGVyTm9kZShjb250ZXh0LCBpbXBvcnRFbnRyeSwgcmFua3MsIGltcG9ydGVkLCBleGNsdWRlZEltcG9ydFR5cGVzKSB7XG4gIGNvbnN0IHJhbmsgPSBjb21wdXRlUmFuayhjb250ZXh0LCByYW5rcywgaW1wb3J0RW50cnksIGV4Y2x1ZGVkSW1wb3J0VHlwZXMpO1xuICBpZiAocmFuayAhPT0gLTEpIHtcbiAgICBpbXBvcnRlZC5wdXNoKHsgLi4uaW1wb3J0RW50cnksIHJhbmsgfSk7XG4gIH1cbn1cblxuZnVuY3Rpb24gZ2V0UmVxdWlyZUJsb2NrKG5vZGUpIHtcbiAgbGV0IG4gPSBub2RlO1xuICAvLyBIYW5kbGUgY2FzZXMgbGlrZSBgY29uc3QgYmF6ID0gcmVxdWlyZSgnZm9vJykuYmFyLmJhemBcbiAgLy8gYW5kIGBjb25zdCBmb28gPSByZXF1aXJlKCdmb28nKSgpYFxuICB3aGlsZSAoXG4gICAgbi5wYXJlbnQudHlwZSA9PT0gJ01lbWJlckV4cHJlc3Npb24nICYmIG4ucGFyZW50Lm9iamVjdCA9PT0gblxuICAgIHx8IG4ucGFyZW50LnR5cGUgPT09ICdDYWxsRXhwcmVzc2lvbicgJiYgbi5wYXJlbnQuY2FsbGVlID09PSBuXG4gICkge1xuICAgIG4gPSBuLnBhcmVudDtcbiAgfVxuICBpZiAoXG4gICAgbi5wYXJlbnQudHlwZSA9PT0gJ1ZhcmlhYmxlRGVjbGFyYXRvcidcbiAgICAmJiBuLnBhcmVudC5wYXJlbnQudHlwZSA9PT0gJ1ZhcmlhYmxlRGVjbGFyYXRpb24nXG4gICAgJiYgbi5wYXJlbnQucGFyZW50LnBhcmVudC50eXBlID09PSAnUHJvZ3JhbSdcbiAgKSB7XG4gICAgcmV0dXJuIG4ucGFyZW50LnBhcmVudC5wYXJlbnQ7XG4gIH1cbn1cblxuY29uc3QgdHlwZXMgPSBbJ2J1aWx0aW4nLCAnZXh0ZXJuYWwnLCAnaW50ZXJuYWwnLCAndW5rbm93bicsICdwYXJlbnQnLCAnc2libGluZycsICdpbmRleCcsICdvYmplY3QnLCAndHlwZSddO1xuXG4vLyBDcmVhdGVzIGFuIG9iamVjdCB3aXRoIHR5cGUtcmFuayBwYWlycy5cbi8vIEV4YW1wbGU6IHsgaW5kZXg6IDAsIHNpYmxpbmc6IDEsIHBhcmVudDogMSwgZXh0ZXJuYWw6IDEsIGJ1aWx0aW46IDIsIGludGVybmFsOiAyIH1cbi8vIFdpbGwgdGhyb3cgYW4gZXJyb3IgaWYgaXQgY29udGFpbnMgYSB0eXBlIHRoYXQgZG9lcyBub3QgZXhpc3QsIG9yIGhhcyBhIGR1cGxpY2F0ZVxuZnVuY3Rpb24gY29udmVydEdyb3Vwc1RvUmFua3MoZ3JvdXBzKSB7XG4gIGNvbnN0IHJhbmtPYmplY3QgPSBncm91cHMucmVkdWNlKGZ1bmN0aW9uIChyZXMsIGdyb3VwLCBpbmRleCkge1xuICAgIFtdLmNvbmNhdChncm91cCkuZm9yRWFjaChmdW5jdGlvbiAoZ3JvdXBJdGVtKSB7XG4gICAgICBpZiAodHlwZXMuaW5kZXhPZihncm91cEl0ZW0pID09PSAtMSkge1xuICAgICAgICB0aHJvdyBuZXcgRXJyb3IoYEluY29ycmVjdCBjb25maWd1cmF0aW9uIG9mIHRoZSBydWxlOiBVbmtub3duIHR5cGUgXFxgJHtKU09OLnN0cmluZ2lmeShncm91cEl0ZW0pfVxcYGApO1xuICAgICAgfVxuICAgICAgaWYgKHJlc1tncm91cEl0ZW1dICE9PSB1bmRlZmluZWQpIHtcbiAgICAgICAgdGhyb3cgbmV3IEVycm9yKGBJbmNvcnJlY3QgY29uZmlndXJhdGlvbiBvZiB0aGUgcnVsZTogXFxgJHtncm91cEl0ZW19XFxgIGlzIGR1cGxpY2F0ZWRgKTtcbiAgICAgIH1cbiAgICAgIHJlc1tncm91cEl0ZW1dID0gaW5kZXggKiAyO1xuICAgIH0pO1xuICAgIHJldHVybiByZXM7XG4gIH0sIHt9KTtcblxuICBjb25zdCBvbWl0dGVkVHlwZXMgPSB0eXBlcy5maWx0ZXIoZnVuY3Rpb24gKHR5cGUpIHtcbiAgICByZXR1cm4gdHlwZW9mIHJhbmtPYmplY3RbdHlwZV0gPT09ICd1bmRlZmluZWQnO1xuICB9KTtcblxuICBjb25zdCByYW5rcyA9IG9taXR0ZWRUeXBlcy5yZWR1Y2UoZnVuY3Rpb24gKHJlcywgdHlwZSkge1xuICAgIHJlc1t0eXBlXSA9IGdyb3Vwcy5sZW5ndGggKiAyO1xuICAgIHJldHVybiByZXM7XG4gIH0sIHJhbmtPYmplY3QpO1xuXG4gIHJldHVybiB7IGdyb3VwczogcmFua3MsIG9taXR0ZWRUeXBlcyB9O1xufVxuXG5mdW5jdGlvbiBjb252ZXJ0UGF0aEdyb3Vwc0ZvclJhbmtzKHBhdGhHcm91cHMpIHtcbiAgY29uc3QgYWZ0ZXIgPSB7fTtcbiAgY29uc3QgYmVmb3JlID0ge307XG5cbiAgY29uc3QgdHJhbnNmb3JtZWQgPSBwYXRoR3JvdXBzLm1hcCgocGF0aEdyb3VwLCBpbmRleCkgPT4ge1xuICAgIGNvbnN0IHsgZ3JvdXAsIHBvc2l0aW9uOiBwb3NpdGlvblN0cmluZyB9ID0gcGF0aEdyb3VwO1xuICAgIGxldCBwb3NpdGlvbiA9IDA7XG4gICAgaWYgKHBvc2l0aW9uU3RyaW5nID09PSAnYWZ0ZXInKSB7XG4gICAgICBpZiAoIWFmdGVyW2dyb3VwXSkge1xuICAgICAgICBhZnRlcltncm91cF0gPSAxO1xuICAgICAgfVxuICAgICAgcG9zaXRpb24gPSBhZnRlcltncm91cF0rKztcbiAgICB9IGVsc2UgaWYgKHBvc2l0aW9uU3RyaW5nID09PSAnYmVmb3JlJykge1xuICAgICAgaWYgKCFiZWZvcmVbZ3JvdXBdKSB7XG4gICAgICAgIGJlZm9yZVtncm91cF0gPSBbXTtcbiAgICAgIH1cbiAgICAgIGJlZm9yZVtncm91cF0ucHVzaChpbmRleCk7XG4gICAgfVxuXG4gICAgcmV0dXJuIHsgLi4ucGF0aEdyb3VwLCBwb3NpdGlvbiB9O1xuICB9KTtcblxuICBsZXQgbWF4UG9zaXRpb24gPSAxO1xuXG4gIE9iamVjdC5rZXlzKGJlZm9yZSkuZm9yRWFjaCgoZ3JvdXApID0+IHtcbiAgICBjb25zdCBncm91cExlbmd0aCA9IGJlZm9yZVtncm91cF0ubGVuZ3RoO1xuICAgIGJlZm9yZVtncm91cF0uZm9yRWFjaCgoZ3JvdXBJbmRleCwgaW5kZXgpID0+IHtcbiAgICAgIHRyYW5zZm9ybWVkW2dyb3VwSW5kZXhdLnBvc2l0aW9uID0gLTEgKiAoZ3JvdXBMZW5ndGggLSBpbmRleCk7XG4gICAgfSk7XG4gICAgbWF4UG9zaXRpb24gPSBNYXRoLm1heChtYXhQb3NpdGlvbiwgZ3JvdXBMZW5ndGgpO1xuICB9KTtcblxuICBPYmplY3Qua2V5cyhhZnRlcikuZm9yRWFjaCgoa2V5KSA9PiB7XG4gICAgY29uc3QgZ3JvdXBOZXh0UG9zaXRpb24gPSBhZnRlcltrZXldO1xuICAgIG1heFBvc2l0aW9uID0gTWF0aC5tYXgobWF4UG9zaXRpb24sIGdyb3VwTmV4dFBvc2l0aW9uIC0gMSk7XG4gIH0pO1xuXG4gIHJldHVybiB7XG4gICAgcGF0aEdyb3VwczogdHJhbnNmb3JtZWQsXG4gICAgbWF4UG9zaXRpb246IG1heFBvc2l0aW9uID4gMTAgPyBNYXRoLnBvdygxMCwgTWF0aC5jZWlsKE1hdGgubG9nMTAobWF4UG9zaXRpb24pKSkgOiAxMCxcbiAgfTtcbn1cblxuZnVuY3Rpb24gZml4TmV3TGluZUFmdGVySW1wb3J0KGNvbnRleHQsIHByZXZpb3VzSW1wb3J0KSB7XG4gIGNvbnN0IHByZXZSb290ID0gZmluZFJvb3ROb2RlKHByZXZpb3VzSW1wb3J0Lm5vZGUpO1xuICBjb25zdCB0b2tlbnNUb0VuZE9mTGluZSA9IHRha2VUb2tlbnNBZnRlcldoaWxlKFxuICAgIGdldFNvdXJjZUNvZGUoY29udGV4dCksXG4gICAgcHJldlJvb3QsXG4gICAgY29tbWVudE9uU2FtZUxpbmVBcyhwcmV2Um9vdCksXG4gICk7XG5cbiAgbGV0IGVuZE9mTGluZSA9IHByZXZSb290LnJhbmdlWzFdO1xuICBpZiAodG9rZW5zVG9FbmRPZkxpbmUubGVuZ3RoID4gMCkge1xuICAgIGVuZE9mTGluZSA9IHRva2Vuc1RvRW5kT2ZMaW5lW3Rva2Vuc1RvRW5kT2ZMaW5lLmxlbmd0aCAtIDFdLnJhbmdlWzFdO1xuICB9XG4gIHJldHVybiAoZml4ZXIpID0+IGZpeGVyLmluc2VydFRleHRBZnRlclJhbmdlKFtwcmV2Um9vdC5yYW5nZVswXSwgZW5kT2ZMaW5lXSwgJ1xcbicpO1xufVxuXG5mdW5jdGlvbiByZW1vdmVOZXdMaW5lQWZ0ZXJJbXBvcnQoY29udGV4dCwgY3VycmVudEltcG9ydCwgcHJldmlvdXNJbXBvcnQpIHtcbiAgY29uc3Qgc291cmNlQ29kZSA9IGdldFNvdXJjZUNvZGUoY29udGV4dCk7XG4gIGNvbnN0IHByZXZSb290ID0gZmluZFJvb3ROb2RlKHByZXZpb3VzSW1wb3J0Lm5vZGUpO1xuICBjb25zdCBjdXJyUm9vdCA9IGZpbmRSb290Tm9kZShjdXJyZW50SW1wb3J0Lm5vZGUpO1xuICBjb25zdCByYW5nZVRvUmVtb3ZlID0gW1xuICAgIGZpbmRFbmRPZkxpbmVXaXRoQ29tbWVudHMoc291cmNlQ29kZSwgcHJldlJvb3QpLFxuICAgIGZpbmRTdGFydE9mTGluZVdpdGhDb21tZW50cyhzb3VyY2VDb2RlLCBjdXJyUm9vdCksXG4gIF07XG4gIGlmICgoL15cXHMqJC8pLnRlc3Qoc291cmNlQ29kZS50ZXh0LnN1YnN0cmluZyhyYW5nZVRvUmVtb3ZlWzBdLCByYW5nZVRvUmVtb3ZlWzFdKSkpIHtcbiAgICByZXR1cm4gKGZpeGVyKSA9PiBmaXhlci5yZW1vdmVSYW5nZShyYW5nZVRvUmVtb3ZlKTtcbiAgfVxuICByZXR1cm4gdW5kZWZpbmVkO1xufVxuXG5mdW5jdGlvbiBtYWtlTmV3bGluZXNCZXR3ZWVuUmVwb3J0KGNvbnRleHQsIGltcG9ydGVkLCBuZXdsaW5lc0JldHdlZW5JbXBvcnRzLCBkaXN0aW5jdEdyb3VwKSB7XG4gIGNvbnN0IGdldE51bWJlck9mRW1wdHlMaW5lc0JldHdlZW4gPSAoY3VycmVudEltcG9ydCwgcHJldmlvdXNJbXBvcnQpID0+IHtcbiAgICBjb25zdCBsaW5lc0JldHdlZW5JbXBvcnRzID0gZ2V0U291cmNlQ29kZShjb250ZXh0KS5saW5lcy5zbGljZShcbiAgICAgIHByZXZpb3VzSW1wb3J0Lm5vZGUubG9jLmVuZC5saW5lLFxuICAgICAgY3VycmVudEltcG9ydC5ub2RlLmxvYy5zdGFydC5saW5lIC0gMSxcbiAgICApO1xuXG4gICAgcmV0dXJuIGxpbmVzQmV0d2VlbkltcG9ydHMuZmlsdGVyKChsaW5lKSA9PiAhbGluZS50cmltKCkubGVuZ3RoKS5sZW5ndGg7XG4gIH07XG4gIGNvbnN0IGdldElzU3RhcnRPZkRpc3RpbmN0R3JvdXAgPSAoY3VycmVudEltcG9ydCwgcHJldmlvdXNJbXBvcnQpID0+IGN1cnJlbnRJbXBvcnQucmFuayAtIDEgPj0gcHJldmlvdXNJbXBvcnQucmFuaztcbiAgbGV0IHByZXZpb3VzSW1wb3J0ID0gaW1wb3J0ZWRbMF07XG5cbiAgaW1wb3J0ZWQuc2xpY2UoMSkuZm9yRWFjaChmdW5jdGlvbiAoY3VycmVudEltcG9ydCkge1xuICAgIGNvbnN0IGVtcHR5TGluZXNCZXR3ZWVuID0gZ2V0TnVtYmVyT2ZFbXB0eUxpbmVzQmV0d2VlbihjdXJyZW50SW1wb3J0LCBwcmV2aW91c0ltcG9ydCk7XG4gICAgY29uc3QgaXNTdGFydE9mRGlzdGluY3RHcm91cCA9IGdldElzU3RhcnRPZkRpc3RpbmN0R3JvdXAoY3VycmVudEltcG9ydCwgcHJldmlvdXNJbXBvcnQpO1xuXG4gICAgaWYgKG5ld2xpbmVzQmV0d2VlbkltcG9ydHMgPT09ICdhbHdheXMnXG4gICAgICAgIHx8IG5ld2xpbmVzQmV0d2VlbkltcG9ydHMgPT09ICdhbHdheXMtYW5kLWluc2lkZS1ncm91cHMnKSB7XG4gICAgICBpZiAoY3VycmVudEltcG9ydC5yYW5rICE9PSBwcmV2aW91c0ltcG9ydC5yYW5rICYmIGVtcHR5TGluZXNCZXR3ZWVuID09PSAwKSB7XG4gICAgICAgIGlmIChkaXN0aW5jdEdyb3VwIHx8ICFkaXN0aW5jdEdyb3VwICYmIGlzU3RhcnRPZkRpc3RpbmN0R3JvdXApIHtcbiAgICAgICAgICBjb250ZXh0LnJlcG9ydCh7XG4gICAgICAgICAgICBub2RlOiBwcmV2aW91c0ltcG9ydC5ub2RlLFxuICAgICAgICAgICAgbWVzc2FnZTogJ1RoZXJlIHNob3VsZCBiZSBhdCBsZWFzdCBvbmUgZW1wdHkgbGluZSBiZXR3ZWVuIGltcG9ydCBncm91cHMnLFxuICAgICAgICAgICAgZml4OiBmaXhOZXdMaW5lQWZ0ZXJJbXBvcnQoY29udGV4dCwgcHJldmlvdXNJbXBvcnQpLFxuICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgICB9IGVsc2UgaWYgKGVtcHR5TGluZXNCZXR3ZWVuID4gMFxuICAgICAgICAmJiBuZXdsaW5lc0JldHdlZW5JbXBvcnRzICE9PSAnYWx3YXlzLWFuZC1pbnNpZGUtZ3JvdXBzJykge1xuICAgICAgICBpZiAoZGlzdGluY3RHcm91cCAmJiBjdXJyZW50SW1wb3J0LnJhbmsgPT09IHByZXZpb3VzSW1wb3J0LnJhbmsgfHwgIWRpc3RpbmN0R3JvdXAgJiYgIWlzU3RhcnRPZkRpc3RpbmN0R3JvdXApIHtcbiAgICAgICAgICBjb250ZXh0LnJlcG9ydCh7XG4gICAgICAgICAgICBub2RlOiBwcmV2aW91c0ltcG9ydC5ub2RlLFxuICAgICAgICAgICAgbWVzc2FnZTogJ1RoZXJlIHNob3VsZCBiZSBubyBlbXB0eSBsaW5lIHdpdGhpbiBpbXBvcnQgZ3JvdXAnLFxuICAgICAgICAgICAgZml4OiByZW1vdmVOZXdMaW5lQWZ0ZXJJbXBvcnQoY29udGV4dCwgY3VycmVudEltcG9ydCwgcHJldmlvdXNJbXBvcnQpLFxuICAgICAgICAgIH0pO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgfSBlbHNlIGlmIChlbXB0eUxpbmVzQmV0d2VlbiA+IDApIHtcbiAgICAgIGNvbnRleHQucmVwb3J0KHtcbiAgICAgICAgbm9kZTogcHJldmlvdXNJbXBvcnQubm9kZSxcbiAgICAgICAgbWVzc2FnZTogJ1RoZXJlIHNob3VsZCBiZSBubyBlbXB0eSBsaW5lIGJldHdlZW4gaW1wb3J0IGdyb3VwcycsXG4gICAgICAgIGZpeDogcmVtb3ZlTmV3TGluZUFmdGVySW1wb3J0KGNvbnRleHQsIGN1cnJlbnRJbXBvcnQsIHByZXZpb3VzSW1wb3J0KSxcbiAgICAgIH0pO1xuICAgIH1cblxuICAgIHByZXZpb3VzSW1wb3J0ID0gY3VycmVudEltcG9ydDtcbiAgfSk7XG59XG5cbmZ1bmN0aW9uIGdldEFscGhhYmV0aXplQ29uZmlnKG9wdGlvbnMpIHtcbiAgY29uc3QgYWxwaGFiZXRpemUgPSBvcHRpb25zLmFscGhhYmV0aXplIHx8IHt9O1xuICBjb25zdCBvcmRlciA9IGFscGhhYmV0aXplLm9yZGVyIHx8ICdpZ25vcmUnO1xuICBjb25zdCBvcmRlckltcG9ydEtpbmQgPSBhbHBoYWJldGl6ZS5vcmRlckltcG9ydEtpbmQgfHwgJ2lnbm9yZSc7XG4gIGNvbnN0IGNhc2VJbnNlbnNpdGl2ZSA9IGFscGhhYmV0aXplLmNhc2VJbnNlbnNpdGl2ZSB8fCBmYWxzZTtcblxuICByZXR1cm4geyBvcmRlciwgb3JkZXJJbXBvcnRLaW5kLCBjYXNlSW5zZW5zaXRpdmUgfTtcbn1cblxuLy8gVE9ETywgc2VtdmVyLW1ham9yOiBDaGFuZ2UgdGhlIGRlZmF1bHQgb2YgXCJkaXN0aW5jdEdyb3VwXCIgZnJvbSB0cnVlIHRvIGZhbHNlXG5jb25zdCBkZWZhdWx0RGlzdGluY3RHcm91cCA9IHRydWU7XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBtZXRhOiB7XG4gICAgdHlwZTogJ3N1Z2dlc3Rpb24nLFxuICAgIGRvY3M6IHtcbiAgICAgIGNhdGVnb3J5OiAnU3R5bGUgZ3VpZGUnLFxuICAgICAgZGVzY3JpcHRpb246ICdFbmZvcmNlIGEgY29udmVudGlvbiBpbiBtb2R1bGUgaW1wb3J0IG9yZGVyLicsXG4gICAgICB1cmw6IGRvY3NVcmwoJ29yZGVyJyksXG4gICAgfSxcblxuICAgIGZpeGFibGU6ICdjb2RlJyxcbiAgICBzY2hlbWE6IFtcbiAgICAgIHtcbiAgICAgICAgdHlwZTogJ29iamVjdCcsXG4gICAgICAgIHByb3BlcnRpZXM6IHtcbiAgICAgICAgICBncm91cHM6IHtcbiAgICAgICAgICAgIHR5cGU6ICdhcnJheScsXG4gICAgICAgICAgfSxcbiAgICAgICAgICBwYXRoR3JvdXBzRXhjbHVkZWRJbXBvcnRUeXBlczoge1xuICAgICAgICAgICAgdHlwZTogJ2FycmF5JyxcbiAgICAgICAgICB9LFxuICAgICAgICAgIGRpc3RpbmN0R3JvdXA6IHtcbiAgICAgICAgICAgIHR5cGU6ICdib29sZWFuJyxcbiAgICAgICAgICAgIGRlZmF1bHQ6IGRlZmF1bHREaXN0aW5jdEdyb3VwLFxuICAgICAgICAgIH0sXG4gICAgICAgICAgcGF0aEdyb3Vwczoge1xuICAgICAgICAgICAgdHlwZTogJ2FycmF5JyxcbiAgICAgICAgICAgIGl0ZW1zOiB7XG4gICAgICAgICAgICAgIHR5cGU6ICdvYmplY3QnLFxuICAgICAgICAgICAgICBwcm9wZXJ0aWVzOiB7XG4gICAgICAgICAgICAgICAgcGF0dGVybjoge1xuICAgICAgICAgICAgICAgICAgdHlwZTogJ3N0cmluZycsXG4gICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgICBwYXR0ZXJuT3B0aW9uczoge1xuICAgICAgICAgICAgICAgICAgdHlwZTogJ29iamVjdCcsXG4gICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgICBncm91cDoge1xuICAgICAgICAgICAgICAgICAgdHlwZTogJ3N0cmluZycsXG4gICAgICAgICAgICAgICAgICBlbnVtOiB0eXBlcyxcbiAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICAgIHBvc2l0aW9uOiB7XG4gICAgICAgICAgICAgICAgICB0eXBlOiAnc3RyaW5nJyxcbiAgICAgICAgICAgICAgICAgIGVudW06IFsnYWZ0ZXInLCAnYmVmb3JlJ10sXG4gICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgYWRkaXRpb25hbFByb3BlcnRpZXM6IGZhbHNlLFxuICAgICAgICAgICAgICByZXF1aXJlZDogWydwYXR0ZXJuJywgJ2dyb3VwJ10sXG4gICAgICAgICAgICB9LFxuICAgICAgICAgIH0sXG4gICAgICAgICAgJ25ld2xpbmVzLWJldHdlZW4nOiB7XG4gICAgICAgICAgICBlbnVtOiBbXG4gICAgICAgICAgICAgICdpZ25vcmUnLFxuICAgICAgICAgICAgICAnYWx3YXlzJyxcbiAgICAgICAgICAgICAgJ2Fsd2F5cy1hbmQtaW5zaWRlLWdyb3VwcycsXG4gICAgICAgICAgICAgICduZXZlcicsXG4gICAgICAgICAgICBdLFxuICAgICAgICAgIH0sXG4gICAgICAgICAgbmFtZWQ6IHtcbiAgICAgICAgICAgIGRlZmF1bHQ6IGZhbHNlLFxuICAgICAgICAgICAgb25lT2Y6IFt7XG4gICAgICAgICAgICAgIHR5cGU6ICdib29sZWFuJyxcbiAgICAgICAgICAgIH0sIHtcbiAgICAgICAgICAgICAgdHlwZTogJ29iamVjdCcsXG4gICAgICAgICAgICAgIHByb3BlcnRpZXM6IHtcbiAgICAgICAgICAgICAgICBlbmFibGVkOiB7IHR5cGU6ICdib29sZWFuJyB9LFxuICAgICAgICAgICAgICAgIGltcG9ydDogeyB0eXBlOiAnYm9vbGVhbicgfSxcbiAgICAgICAgICAgICAgICBleHBvcnQ6IHsgdHlwZTogJ2Jvb2xlYW4nIH0sXG4gICAgICAgICAgICAgICAgcmVxdWlyZTogeyB0eXBlOiAnYm9vbGVhbicgfSxcbiAgICAgICAgICAgICAgICBjanNFeHBvcnRzOiB7IHR5cGU6ICdib29sZWFuJyB9LFxuICAgICAgICAgICAgICAgIHR5cGVzOiB7XG4gICAgICAgICAgICAgICAgICB0eXBlOiAnc3RyaW5nJyxcbiAgICAgICAgICAgICAgICAgIGVudW06IFtcbiAgICAgICAgICAgICAgICAgICAgJ21peGVkJyxcbiAgICAgICAgICAgICAgICAgICAgJ3R5cGVzLWZpcnN0JyxcbiAgICAgICAgICAgICAgICAgICAgJ3R5cGVzLWxhc3QnLFxuICAgICAgICAgICAgICAgICAgXSxcbiAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICBhZGRpdGlvbmFsUHJvcGVydGllczogZmFsc2UsXG4gICAgICAgICAgICB9XSxcbiAgICAgICAgICB9LFxuICAgICAgICAgIGFscGhhYmV0aXplOiB7XG4gICAgICAgICAgICB0eXBlOiAnb2JqZWN0JyxcbiAgICAgICAgICAgIHByb3BlcnRpZXM6IHtcbiAgICAgICAgICAgICAgY2FzZUluc2Vuc2l0aXZlOiB7XG4gICAgICAgICAgICAgICAgdHlwZTogJ2Jvb2xlYW4nLFxuICAgICAgICAgICAgICAgIGRlZmF1bHQ6IGZhbHNlLFxuICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICBvcmRlcjoge1xuICAgICAgICAgICAgICAgIGVudW06IFsnaWdub3JlJywgJ2FzYycsICdkZXNjJ10sXG4gICAgICAgICAgICAgICAgZGVmYXVsdDogJ2lnbm9yZScsXG4gICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICAgIG9yZGVySW1wb3J0S2luZDoge1xuICAgICAgICAgICAgICAgIGVudW06IFsnaWdub3JlJywgJ2FzYycsICdkZXNjJ10sXG4gICAgICAgICAgICAgICAgZGVmYXVsdDogJ2lnbm9yZScsXG4gICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICB9LFxuICAgICAgICAgICAgYWRkaXRpb25hbFByb3BlcnRpZXM6IGZhbHNlLFxuICAgICAgICAgIH0sXG4gICAgICAgICAgd2Fybk9uVW5hc3NpZ25lZEltcG9ydHM6IHtcbiAgICAgICAgICAgIHR5cGU6ICdib29sZWFuJyxcbiAgICAgICAgICAgIGRlZmF1bHQ6IGZhbHNlLFxuICAgICAgICAgIH0sXG4gICAgICAgIH0sXG4gICAgICAgIGFkZGl0aW9uYWxQcm9wZXJ0aWVzOiBmYWxzZSxcbiAgICAgIH0sXG4gICAgXSxcbiAgfSxcblxuICBjcmVhdGUoY29udGV4dCkge1xuICAgIGNvbnN0IG9wdGlvbnMgPSBjb250ZXh0Lm9wdGlvbnNbMF0gfHwge307XG4gICAgY29uc3QgbmV3bGluZXNCZXR3ZWVuSW1wb3J0cyA9IG9wdGlvbnNbJ25ld2xpbmVzLWJldHdlZW4nXSB8fCAnaWdub3JlJztcbiAgICBjb25zdCBwYXRoR3JvdXBzRXhjbHVkZWRJbXBvcnRUeXBlcyA9IG5ldyBTZXQob3B0aW9ucy5wYXRoR3JvdXBzRXhjbHVkZWRJbXBvcnRUeXBlcyB8fCBbJ2J1aWx0aW4nLCAnZXh0ZXJuYWwnLCAnb2JqZWN0J10pO1xuXG4gICAgY29uc3QgbmFtZWQgPSB7XG4gICAgICB0eXBlczogJ21peGVkJyxcbiAgICAgIC4uLnR5cGVvZiBvcHRpb25zLm5hbWVkID09PSAnb2JqZWN0JyA/IHtcbiAgICAgICAgLi4ub3B0aW9ucy5uYW1lZCxcbiAgICAgICAgaW1wb3J0OiAnaW1wb3J0JyBpbiBvcHRpb25zLm5hbWVkID8gb3B0aW9ucy5uYW1lZC5pbXBvcnQgOiBvcHRpb25zLm5hbWVkLmVuYWJsZWQsXG4gICAgICAgIGV4cG9ydDogJ2V4cG9ydCcgaW4gb3B0aW9ucy5uYW1lZCA/IG9wdGlvbnMubmFtZWQuZXhwb3J0IDogb3B0aW9ucy5uYW1lZC5lbmFibGVkLFxuICAgICAgICByZXF1aXJlOiAncmVxdWlyZScgaW4gb3B0aW9ucy5uYW1lZCA/IG9wdGlvbnMubmFtZWQucmVxdWlyZSA6IG9wdGlvbnMubmFtZWQuZW5hYmxlZCxcbiAgICAgICAgY2pzRXhwb3J0czogJ2Nqc0V4cG9ydHMnIGluIG9wdGlvbnMubmFtZWQgPyBvcHRpb25zLm5hbWVkLmNqc0V4cG9ydHMgOiBvcHRpb25zLm5hbWVkLmVuYWJsZWQsXG4gICAgICB9IDoge1xuICAgICAgICBpbXBvcnQ6IG9wdGlvbnMubmFtZWQsXG4gICAgICAgIGV4cG9ydDogb3B0aW9ucy5uYW1lZCxcbiAgICAgICAgcmVxdWlyZTogb3B0aW9ucy5uYW1lZCxcbiAgICAgICAgY2pzRXhwb3J0czogb3B0aW9ucy5uYW1lZCxcbiAgICAgIH0sXG4gICAgfTtcblxuICAgIGNvbnN0IG5hbWVkR3JvdXBzID0gbmFtZWQudHlwZXMgPT09ICdtaXhlZCcgPyBbXSA6IG5hbWVkLnR5cGVzID09PSAndHlwZXMtbGFzdCcgPyBbJ3ZhbHVlJ10gOiBbJ3R5cGUnXTtcbiAgICBjb25zdCBhbHBoYWJldGl6ZSA9IGdldEFscGhhYmV0aXplQ29uZmlnKG9wdGlvbnMpO1xuICAgIGNvbnN0IGRpc3RpbmN0R3JvdXAgPSBvcHRpb25zLmRpc3RpbmN0R3JvdXAgPT0gbnVsbCA/IGRlZmF1bHREaXN0aW5jdEdyb3VwIDogISFvcHRpb25zLmRpc3RpbmN0R3JvdXA7XG4gICAgbGV0IHJhbmtzO1xuXG4gICAgdHJ5IHtcbiAgICAgIGNvbnN0IHsgcGF0aEdyb3VwcywgbWF4UG9zaXRpb24gfSA9IGNvbnZlcnRQYXRoR3JvdXBzRm9yUmFua3Mob3B0aW9ucy5wYXRoR3JvdXBzIHx8IFtdKTtcbiAgICAgIGNvbnN0IHsgZ3JvdXBzLCBvbWl0dGVkVHlwZXMgfSA9IGNvbnZlcnRHcm91cHNUb1JhbmtzKG9wdGlvbnMuZ3JvdXBzIHx8IGRlZmF1bHRHcm91cHMpO1xuICAgICAgcmFua3MgPSB7XG4gICAgICAgIGdyb3VwcyxcbiAgICAgICAgb21pdHRlZFR5cGVzLFxuICAgICAgICBwYXRoR3JvdXBzLFxuICAgICAgICBtYXhQb3NpdGlvbixcbiAgICAgIH07XG4gICAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICAgIC8vIE1hbGZvcm1lZCBjb25maWd1cmF0aW9uXG4gICAgICByZXR1cm4ge1xuICAgICAgICBQcm9ncmFtKG5vZGUpIHtcbiAgICAgICAgICBjb250ZXh0LnJlcG9ydChub2RlLCBlcnJvci5tZXNzYWdlKTtcbiAgICAgICAgfSxcbiAgICAgIH07XG4gICAgfVxuICAgIGNvbnN0IGltcG9ydE1hcCA9IG5ldyBNYXAoKTtcbiAgICBjb25zdCBleHBvcnRNYXAgPSBuZXcgTWFwKCk7XG5cbiAgICBmdW5jdGlvbiBnZXRCbG9ja0ltcG9ydHMobm9kZSkge1xuICAgICAgaWYgKCFpbXBvcnRNYXAuaGFzKG5vZGUpKSB7XG4gICAgICAgIGltcG9ydE1hcC5zZXQobm9kZSwgW10pO1xuICAgICAgfVxuICAgICAgcmV0dXJuIGltcG9ydE1hcC5nZXQobm9kZSk7XG4gICAgfVxuXG4gICAgZnVuY3Rpb24gZ2V0QmxvY2tFeHBvcnRzKG5vZGUpIHtcbiAgICAgIGlmICghZXhwb3J0TWFwLmhhcyhub2RlKSkge1xuICAgICAgICBleHBvcnRNYXAuc2V0KG5vZGUsIFtdKTtcbiAgICAgIH1cbiAgICAgIHJldHVybiBleHBvcnRNYXAuZ2V0KG5vZGUpO1xuICAgIH1cblxuICAgIGZ1bmN0aW9uIG1ha2VOYW1lZE9yZGVyUmVwb3J0KGNvbnRleHQsIG5hbWVkSW1wb3J0cykge1xuICAgICAgaWYgKG5hbWVkSW1wb3J0cy5sZW5ndGggPiAxKSB7XG4gICAgICAgIGNvbnN0IGltcG9ydHMgPSBuYW1lZEltcG9ydHMubWFwKFxuICAgICAgICAgIChuYW1lZEltcG9ydCkgPT4ge1xuICAgICAgICAgICAgY29uc3Qga2luZCA9IG5hbWVkSW1wb3J0LmtpbmQgfHwgJ3ZhbHVlJztcbiAgICAgICAgICAgIGNvbnN0IHJhbmsgPSBuYW1lZEdyb3Vwcy5maW5kSW5kZXgoKGVudHJ5KSA9PiBbXS5jb25jYXQoZW50cnkpLmluZGV4T2Yoa2luZCkgPiAtMSk7XG5cbiAgICAgICAgICAgIHJldHVybiB7XG4gICAgICAgICAgICAgIGRpc3BsYXlOYW1lOiBuYW1lZEltcG9ydC52YWx1ZSxcbiAgICAgICAgICAgICAgcmFuazogcmFuayA9PT0gLTEgPyBuYW1lZEdyb3Vwcy5sZW5ndGggOiByYW5rLFxuICAgICAgICAgICAgICAuLi5uYW1lZEltcG9ydCxcbiAgICAgICAgICAgICAgdmFsdWU6IGAke25hbWVkSW1wb3J0LnZhbHVlfToke25hbWVkSW1wb3J0LmFsaWFzIHx8ICcnfWAsXG4gICAgICAgICAgICB9O1xuICAgICAgICAgIH0pO1xuXG4gICAgICAgIGlmIChhbHBoYWJldGl6ZS5vcmRlciAhPT0gJ2lnbm9yZScpIHtcbiAgICAgICAgICBtdXRhdGVSYW5rc1RvQWxwaGFiZXRpemUoaW1wb3J0cywgYWxwaGFiZXRpemUpO1xuICAgICAgICB9XG5cbiAgICAgICAgbWFrZU91dE9mT3JkZXJSZXBvcnQoY29udGV4dCwgaW1wb3J0cywgY2F0ZWdvcmllcy5uYW1lZCk7XG4gICAgICB9XG4gICAgfVxuXG4gICAgcmV0dXJuIHtcbiAgICAgIEltcG9ydERlY2xhcmF0aW9uKG5vZGUpIHtcbiAgICAgICAgLy8gSWdub3JpbmcgdW5hc3NpZ25lZCBpbXBvcnRzIHVubGVzcyB3YXJuT25VbmFzc2lnbmVkSW1wb3J0cyBpcyBzZXRcbiAgICAgICAgaWYgKG5vZGUuc3BlY2lmaWVycy5sZW5ndGggfHwgb3B0aW9ucy53YXJuT25VbmFzc2lnbmVkSW1wb3J0cykge1xuICAgICAgICAgIGNvbnN0IG5hbWUgPSBub2RlLnNvdXJjZS52YWx1ZTtcbiAgICAgICAgICByZWdpc3Rlck5vZGUoXG4gICAgICAgICAgICBjb250ZXh0LFxuICAgICAgICAgICAge1xuICAgICAgICAgICAgICBub2RlLFxuICAgICAgICAgICAgICB2YWx1ZTogbmFtZSxcbiAgICAgICAgICAgICAgZGlzcGxheU5hbWU6IG5hbWUsXG4gICAgICAgICAgICAgIHR5cGU6ICdpbXBvcnQnLFxuICAgICAgICAgICAgfSxcbiAgICAgICAgICAgIHJhbmtzLFxuICAgICAgICAgICAgZ2V0QmxvY2tJbXBvcnRzKG5vZGUucGFyZW50KSxcbiAgICAgICAgICAgIHBhdGhHcm91cHNFeGNsdWRlZEltcG9ydFR5cGVzLFxuICAgICAgICAgICk7XG5cbiAgICAgICAgICBpZiAobmFtZWQuaW1wb3J0KSB7XG4gICAgICAgICAgICBtYWtlTmFtZWRPcmRlclJlcG9ydChcbiAgICAgICAgICAgICAgY29udGV4dCxcbiAgICAgICAgICAgICAgbm9kZS5zcGVjaWZpZXJzLmZpbHRlcihcbiAgICAgICAgICAgICAgICAoc3BlY2lmaWVyKSA9PiBzcGVjaWZpZXIudHlwZSA9PT0gJ0ltcG9ydFNwZWNpZmllcicpLm1hcChcbiAgICAgICAgICAgICAgICAoc3BlY2lmaWVyKSA9PiAoe1xuICAgICAgICAgICAgICAgICAgbm9kZTogc3BlY2lmaWVyLFxuICAgICAgICAgICAgICAgICAgdmFsdWU6IHNwZWNpZmllci5pbXBvcnRlZC5uYW1lLFxuICAgICAgICAgICAgICAgICAgdHlwZTogJ2ltcG9ydCcsXG4gICAgICAgICAgICAgICAgICBraW5kOiBzcGVjaWZpZXIuaW1wb3J0S2luZCxcbiAgICAgICAgICAgICAgICAgIC4uLnNwZWNpZmllci5sb2NhbC5yYW5nZVswXSAhPT0gc3BlY2lmaWVyLmltcG9ydGVkLnJhbmdlWzBdICYmIHtcbiAgICAgICAgICAgICAgICAgICAgYWxpYXM6IHNwZWNpZmllci5sb2NhbC5uYW1lLFxuICAgICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgICB9KSxcbiAgICAgICAgICAgICAgKSxcbiAgICAgICAgICAgICk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9LFxuICAgICAgVFNJbXBvcnRFcXVhbHNEZWNsYXJhdGlvbihub2RlKSB7XG4gICAgICAgIC8vIHNraXAgXCJleHBvcnQgaW1wb3J0XCJzXG4gICAgICAgIGlmIChub2RlLmlzRXhwb3J0KSB7XG4gICAgICAgICAgcmV0dXJuO1xuICAgICAgICB9XG5cbiAgICAgICAgbGV0IGRpc3BsYXlOYW1lO1xuICAgICAgICBsZXQgdmFsdWU7XG4gICAgICAgIGxldCB0eXBlO1xuICAgICAgICBpZiAobm9kZS5tb2R1bGVSZWZlcmVuY2UudHlwZSA9PT0gJ1RTRXh0ZXJuYWxNb2R1bGVSZWZlcmVuY2UnKSB7XG4gICAgICAgICAgdmFsdWUgPSBub2RlLm1vZHVsZVJlZmVyZW5jZS5leHByZXNzaW9uLnZhbHVlO1xuICAgICAgICAgIGRpc3BsYXlOYW1lID0gdmFsdWU7XG4gICAgICAgICAgdHlwZSA9ICdpbXBvcnQnO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIHZhbHVlID0gJyc7XG4gICAgICAgICAgZGlzcGxheU5hbWUgPSBnZXRTb3VyY2VDb2RlKGNvbnRleHQpLmdldFRleHQobm9kZS5tb2R1bGVSZWZlcmVuY2UpO1xuICAgICAgICAgIHR5cGUgPSAnaW1wb3J0Om9iamVjdCc7XG4gICAgICAgIH1cblxuICAgICAgICByZWdpc3Rlck5vZGUoXG4gICAgICAgICAgY29udGV4dCxcbiAgICAgICAgICB7XG4gICAgICAgICAgICBub2RlLFxuICAgICAgICAgICAgdmFsdWUsXG4gICAgICAgICAgICBkaXNwbGF5TmFtZSxcbiAgICAgICAgICAgIHR5cGUsXG4gICAgICAgICAgfSxcbiAgICAgICAgICByYW5rcyxcbiAgICAgICAgICBnZXRCbG9ja0ltcG9ydHMobm9kZS5wYXJlbnQpLFxuICAgICAgICAgIHBhdGhHcm91cHNFeGNsdWRlZEltcG9ydFR5cGVzLFxuICAgICAgICApO1xuICAgICAgfSxcbiAgICAgIENhbGxFeHByZXNzaW9uKG5vZGUpIHtcbiAgICAgICAgaWYgKCFpc1N0YXRpY1JlcXVpcmUobm9kZSkpIHtcbiAgICAgICAgICByZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgY29uc3QgYmxvY2sgPSBnZXRSZXF1aXJlQmxvY2sobm9kZSk7XG4gICAgICAgIGlmICghYmxvY2spIHtcbiAgICAgICAgICByZXR1cm47XG4gICAgICAgIH1cbiAgICAgICAgY29uc3QgbmFtZSA9IG5vZGUuYXJndW1lbnRzWzBdLnZhbHVlO1xuICAgICAgICByZWdpc3Rlck5vZGUoXG4gICAgICAgICAgY29udGV4dCxcbiAgICAgICAgICB7XG4gICAgICAgICAgICBub2RlLFxuICAgICAgICAgICAgdmFsdWU6IG5hbWUsXG4gICAgICAgICAgICBkaXNwbGF5TmFtZTogbmFtZSxcbiAgICAgICAgICAgIHR5cGU6ICdyZXF1aXJlJyxcbiAgICAgICAgICB9LFxuICAgICAgICAgIHJhbmtzLFxuICAgICAgICAgIGdldEJsb2NrSW1wb3J0cyhibG9jayksXG4gICAgICAgICAgcGF0aEdyb3Vwc0V4Y2x1ZGVkSW1wb3J0VHlwZXMsXG4gICAgICAgICk7XG4gICAgICB9LFxuICAgICAgLi4ubmFtZWQucmVxdWlyZSAmJiB7XG4gICAgICAgIFZhcmlhYmxlRGVjbGFyYXRvcihub2RlKSB7XG4gICAgICAgICAgaWYgKG5vZGUuaWQudHlwZSA9PT0gJ09iamVjdFBhdHRlcm4nICYmIGlzUmVxdWlyZUV4cHJlc3Npb24obm9kZS5pbml0KSkge1xuICAgICAgICAgICAgZm9yIChsZXQgaSA9IDA7IGkgPCBub2RlLmlkLnByb3BlcnRpZXMubGVuZ3RoOyBpKyspIHtcbiAgICAgICAgICAgICAgaWYgKFxuICAgICAgICAgICAgICAgIG5vZGUuaWQucHJvcGVydGllc1tpXS5rZXkudHlwZSAhPT0gJ0lkZW50aWZpZXInXG4gICAgICAgICAgICAgICAgfHwgbm9kZS5pZC5wcm9wZXJ0aWVzW2ldLnZhbHVlLnR5cGUgIT09ICdJZGVudGlmaWVyJ1xuICAgICAgICAgICAgICApIHtcbiAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIG1ha2VOYW1lZE9yZGVyUmVwb3J0KFxuICAgICAgICAgICAgICBjb250ZXh0LFxuICAgICAgICAgICAgICBub2RlLmlkLnByb3BlcnRpZXMubWFwKChwcm9wKSA9PiAoe1xuICAgICAgICAgICAgICAgIG5vZGU6IHByb3AsXG4gICAgICAgICAgICAgICAgdmFsdWU6IHByb3Aua2V5Lm5hbWUsXG4gICAgICAgICAgICAgICAgdHlwZTogJ3JlcXVpcmUnLFxuICAgICAgICAgICAgICAgIC4uLnByb3Aua2V5LnJhbmdlWzBdICE9PSBwcm9wLnZhbHVlLnJhbmdlWzBdICYmIHtcbiAgICAgICAgICAgICAgICAgIGFsaWFzOiBwcm9wLnZhbHVlLm5hbWUsXG4gICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgICAgfSkpLFxuICAgICAgICAgICAgKTtcbiAgICAgICAgICB9XG4gICAgICAgIH0sXG4gICAgICB9LFxuICAgICAgLi4ubmFtZWQuZXhwb3J0ICYmIHtcbiAgICAgICAgRXhwb3J0TmFtZWREZWNsYXJhdGlvbihub2RlKSB7XG4gICAgICAgICAgbWFrZU5hbWVkT3JkZXJSZXBvcnQoXG4gICAgICAgICAgICBjb250ZXh0LFxuICAgICAgICAgICAgbm9kZS5zcGVjaWZpZXJzLm1hcCgoc3BlY2lmaWVyKSA9PiAoe1xuICAgICAgICAgICAgICBub2RlOiBzcGVjaWZpZXIsXG4gICAgICAgICAgICAgIHZhbHVlOiBzcGVjaWZpZXIubG9jYWwubmFtZSxcbiAgICAgICAgICAgICAgdHlwZTogJ2V4cG9ydCcsXG4gICAgICAgICAgICAgIGtpbmQ6IHNwZWNpZmllci5leHBvcnRLaW5kLFxuICAgICAgICAgICAgICAuLi5zcGVjaWZpZXIubG9jYWwucmFuZ2VbMF0gIT09IHNwZWNpZmllci5leHBvcnRlZC5yYW5nZVswXSAmJiB7XG4gICAgICAgICAgICAgICAgYWxpYXM6IHNwZWNpZmllci5leHBvcnRlZC5uYW1lLFxuICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgfSkpLFxuICAgICAgICAgICk7XG4gICAgICAgIH0sXG4gICAgICB9LFxuICAgICAgLi4ubmFtZWQuY2pzRXhwb3J0cyAmJiB7XG4gICAgICAgIEFzc2lnbm1lbnRFeHByZXNzaW9uKG5vZGUpIHtcbiAgICAgICAgICBpZiAobm9kZS5wYXJlbnQudHlwZSA9PT0gJ0V4cHJlc3Npb25TdGF0ZW1lbnQnKSB7XG4gICAgICAgICAgICBpZiAoaXNDSlNFeHBvcnRzKGNvbnRleHQsIG5vZGUubGVmdCkpIHtcbiAgICAgICAgICAgICAgaWYgKG5vZGUucmlnaHQudHlwZSA9PT0gJ09iamVjdEV4cHJlc3Npb24nKSB7XG4gICAgICAgICAgICAgICAgZm9yIChsZXQgaSA9IDA7IGkgPCBub2RlLnJpZ2h0LnByb3BlcnRpZXMubGVuZ3RoOyBpKyspIHtcbiAgICAgICAgICAgICAgICAgIGlmIChcbiAgICAgICAgICAgICAgICAgICAgbm9kZS5yaWdodC5wcm9wZXJ0aWVzW2ldLmtleS50eXBlICE9PSAnSWRlbnRpZmllcidcbiAgICAgICAgICAgICAgICAgICAgfHwgbm9kZS5yaWdodC5wcm9wZXJ0aWVzW2ldLnZhbHVlLnR5cGUgIT09ICdJZGVudGlmaWVyJ1xuICAgICAgICAgICAgICAgICAgKSB7XG4gICAgICAgICAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICB9XG5cbiAgICAgICAgICAgICAgICBtYWtlTmFtZWRPcmRlclJlcG9ydChcbiAgICAgICAgICAgICAgICAgIGNvbnRleHQsXG4gICAgICAgICAgICAgICAgICBub2RlLnJpZ2h0LnByb3BlcnRpZXMubWFwKChwcm9wKSA9PiAoe1xuICAgICAgICAgICAgICAgICAgICBub2RlOiBwcm9wLFxuICAgICAgICAgICAgICAgICAgICB2YWx1ZTogcHJvcC5rZXkubmFtZSxcbiAgICAgICAgICAgICAgICAgICAgdHlwZTogJ2V4cG9ydCcsXG4gICAgICAgICAgICAgICAgICAgIC4uLnByb3Aua2V5LnJhbmdlWzBdICE9PSBwcm9wLnZhbHVlLnJhbmdlWzBdICYmIHtcbiAgICAgICAgICAgICAgICAgICAgICBhbGlhczogcHJvcC52YWx1ZS5uYW1lLFxuICAgICAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICAgICAgfSkpLFxuICAgICAgICAgICAgICAgICk7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICAgIGNvbnN0IG5hbWVQYXJ0cyA9IGdldE5hbWVkQ0pTRXhwb3J0cyhjb250ZXh0LCBub2RlLmxlZnQpO1xuICAgICAgICAgICAgICBpZiAobmFtZVBhcnRzICYmIG5hbWVQYXJ0cy5sZW5ndGggPiAwKSB7XG4gICAgICAgICAgICAgICAgY29uc3QgbmFtZSA9IG5hbWVQYXJ0cy5qb2luKCcuJyk7XG4gICAgICAgICAgICAgICAgZ2V0QmxvY2tFeHBvcnRzKG5vZGUucGFyZW50LnBhcmVudCkucHVzaCh7XG4gICAgICAgICAgICAgICAgICBub2RlLFxuICAgICAgICAgICAgICAgICAgdmFsdWU6IG5hbWUsXG4gICAgICAgICAgICAgICAgICBkaXNwbGF5TmFtZTogbmFtZSxcbiAgICAgICAgICAgICAgICAgIHR5cGU6ICdleHBvcnQnLFxuICAgICAgICAgICAgICAgICAgcmFuazogMCxcbiAgICAgICAgICAgICAgICB9KTtcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cbiAgICAgICAgfSxcbiAgICAgIH0sXG4gICAgICAnUHJvZ3JhbTpleGl0JygpIHtcbiAgICAgICAgaW1wb3J0TWFwLmZvckVhY2goKGltcG9ydGVkKSA9PiB7XG4gICAgICAgICAgaWYgKG5ld2xpbmVzQmV0d2VlbkltcG9ydHMgIT09ICdpZ25vcmUnKSB7XG4gICAgICAgICAgICBtYWtlTmV3bGluZXNCZXR3ZWVuUmVwb3J0KGNvbnRleHQsIGltcG9ydGVkLCBuZXdsaW5lc0JldHdlZW5JbXBvcnRzLCBkaXN0aW5jdEdyb3VwKTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBpZiAoYWxwaGFiZXRpemUub3JkZXIgIT09ICdpZ25vcmUnKSB7XG4gICAgICAgICAgICBtdXRhdGVSYW5rc1RvQWxwaGFiZXRpemUoaW1wb3J0ZWQsIGFscGhhYmV0aXplKTtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBtYWtlT3V0T2ZPcmRlclJlcG9ydChjb250ZXh0LCBpbXBvcnRlZCwgY2F0ZWdvcmllcy5pbXBvcnQpO1xuICAgICAgICB9KTtcblxuICAgICAgICBleHBvcnRNYXAuZm9yRWFjaCgoZXhwb3J0ZWQpID0+IHtcbiAgICAgICAgICBpZiAoYWxwaGFiZXRpemUub3JkZXIgIT09ICdpZ25vcmUnKSB7XG4gICAgICAgICAgICBtdXRhdGVSYW5rc1RvQWxwaGFiZXRpemUoZXhwb3J0ZWQsIGFscGhhYmV0aXplKTtcbiAgICAgICAgICAgIG1ha2VPdXRPZk9yZGVyUmVwb3J0KGNvbnRleHQsIGV4cG9ydGVkLCBjYXRlZ29yaWVzLmV4cG9ydHMpO1xuICAgICAgICAgIH1cbiAgICAgICAgfSk7XG5cbiAgICAgICAgaW1wb3J0TWFwLmNsZWFyKCk7XG4gICAgICAgIGV4cG9ydE1hcC5jbGVhcigpO1xuICAgICAgfSxcbiAgICB9O1xuICB9LFxufTtcbiJdfQ==