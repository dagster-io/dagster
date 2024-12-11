import {ParserRuleContext} from 'antlr4ts';

export const removeQuotesFromString = (value: string) => {
  if (value.length > 1 && value[0] === '"' && value[value.length - 1] === '"') {
    return value.slice(1, -1);
  }
  return value;
};

export function getValueNodeValue(ctx: ParserRuleContext) {
  let nodeValue = ctx.text;
  const nodeType = ctx.constructor.name;
  if (nodeType === 'QuotedStringValueContext') {
    nodeValue = nodeValue.slice(1, -1);
  } else if (nodeType === 'IncompleteLeftQuotedStringValueContext') {
    nodeValue = nodeValue.slice(1);
  } else if (nodeType === 'IncompleteRightQuotedStringValueContext') {
    nodeValue = nodeValue.slice(0, -1);
  }
  return nodeValue.trim();
}

export function isInsideExpressionlessParenthesizedExpression(context: ParserRuleContext) {
  if (context.parent) {
    const nodeType = context.parent.constructor.name;
    if (nodeType.startsWith('Unclosed')) {
      return true;
    }
    return isInsideExpressionlessParenthesizedExpression(context.parent);
  }
  return false;
}
