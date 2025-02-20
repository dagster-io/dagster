import {ParserRuleContext} from 'antlr4ts';

import {
  AttributeValueContext,
  IncompleteLeftQuotedStringValueContext,
  IncompleteRightQuotedStringValueContext,
  QuotedStringValueContext,
  UnclosedExpressionlessFunctionExpressionContext,
  UnclosedFunctionExpressionContext,
  UnclosedParenthesizedExpressionContext,
  UnquotedStringValueContext,
} from './generated/SelectionAutoCompleteParser';

export const removeQuotesFromString = (value: string) => {
  if (value.length > 1 && value[0] === '"' && value[value.length - 1] === '"') {
    return value.slice(1, -1);
  }
  return value;
};

export function getValueNodeValue(ctx: ParserRuleContext | null) {
  switch (ctx?.constructor.name) {
    case UnquotedStringValueContext.name:
      return ctx.text;
    case IncompleteLeftQuotedStringValueContext.name:
      return ctx.text.slice(1);
    case IncompleteRightQuotedStringValueContext.name:
      return ctx.text.slice(0, -1);
    case QuotedStringValueContext.name:
      return ctx.text.slice(1, -1);
    case AttributeValueContext.name:
      return getValueNodeValue((ctx as AttributeValueContext).value());
    default:
      return ctx?.text ?? '';
  }
}

export function isInsideExpressionlessParenthesizedExpression(
  context: ParserRuleContext | undefined,
) {
  const parent = context?.parent;
  if (parent) {
    const nodeType = parent.constructor.name;
    switch (nodeType) {
      case UnclosedParenthesizedExpressionContext.name:
      case UnclosedFunctionExpressionContext.name:
      case UnclosedExpressionlessFunctionExpressionContext.name:
        return true;
      default:
        return isInsideExpressionlessParenthesizedExpression(parent);
    }
  }
  return false;
}
