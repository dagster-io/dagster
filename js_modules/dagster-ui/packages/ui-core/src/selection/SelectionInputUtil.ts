import {ParserRuleContext} from 'antlr4ng';

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
    return ctx.getText();
  }
  if (ctx instanceof IncompleteLeftQuotedStringValueContext) {
    return ctx.getText().slice(1);
  }
  if (ctx instanceof IncompleteRightQuotedStringValueContext) {
    return ctx.getText().slice(0, -1);
  }
  if (ctx instanceof QuotedStringValueContext) {
    return ctx.getText().slice(1, -1);
  }
  if (ctx instanceof AttributeValueContext) {
    return getValueNodeValue(ctx.value());
  }
  return ctx?.getText() ?? '';
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
