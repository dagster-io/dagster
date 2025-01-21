import {ParserRuleContext} from 'antlr4ts';

export const removeQuotesFromString = (value: string) => {
  if (value.length > 1 && value[0] === '"' && value[value.length - 1] === '"') {
    return value.slice(1, -1);
  }
  return value;
};

export function getValueNodeValue(ctx: ParserRuleContext | null) {
  switch (ctx?.constructor.name) {
    case 'UnquotedStringValueContext':
      return ctx.text;
    case 'IncompleteLeftQuotedStringValueContext':
      return ctx.text.slice(1);
    case 'IncompleteRightQuotedStringValueContext':
      return ctx.text.slice(0, -1);
    case 'QuotedStringValueContext':
      return ctx.text.slice(1, -1);
    default:
      return ctx?.text ?? '';
  }
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
