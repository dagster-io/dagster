import {ParserRuleContext} from 'antlr4ts';

import {
  AttributeValueContext,
  DigitsValueContext,
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
  if (ctx instanceof DigitsValueContext || ctx instanceof UnquotedStringValueContext) {
    return ctx.text;
  }
  if (ctx instanceof IncompleteLeftQuotedStringValueContext) {
    return ctx.text.slice(1);
  }
  if (ctx instanceof IncompleteRightQuotedStringValueContext) {
    return ctx.text.slice(0, -1);
  }
  if (ctx instanceof QuotedStringValueContext) {
    return ctx.text.slice(1, -1);
  }
  if (ctx instanceof AttributeValueContext) {
    return getValueNodeValue(ctx.value());
  }
  return ctx?.text ?? '';
}

export function isInsideExpressionlessParenthesizedExpression(
  context: ParserRuleContext | undefined,
) {
  const parent = context?.parent;
  if (parent) {
    if (parent instanceof UnclosedParenthesizedExpressionContext) {
      return true;
    }
    if (parent instanceof UnclosedFunctionExpressionContext) {
      return true;
    }
    if (parent instanceof UnclosedExpressionlessFunctionExpressionContext) {
      return true;
    }
    return isInsideExpressionlessParenthesizedExpression(parent);
  }
  return false;
}
