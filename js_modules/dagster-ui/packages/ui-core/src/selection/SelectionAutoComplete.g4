grammar SelectionAutoComplete;

start: expr EOF;

/*
 * Apply a specific whitespace parser rule (e.g., afterLogicalOperatorWhitespace,
 * afterExpressionWhitespace) after every leaf node. This strategy prevents multiple parser rules
 * from conflicting over the same whitespace. Add more whitespace types to adjust autocomplete
 * boundary behavior within and after tokens.
 */
expr:
	traversalAllowedExpr										# TraversalAllowedExpression
	| upTraversalExpr traversalAllowedExpr downTraversalExpr	# UpAndDownTraversalExpression
	| upTraversalExpr traversalAllowedExpr						# UpTraversalExpression
	| traversalAllowedExpr downTraversalExpr					# DownTraversalExpression
	| notToken postNotOperatorWhitespace expr					# NotExpression
	| expr andToken postLogicalOperatorWhitespace expr			# AndExpression
	| expr orToken postLogicalOperatorWhitespace expr			# OrExpression
	| expr commaToken expr										# CommaExpressionWrapper1
	| expr andToken postLogicalOperatorWhitespace				# IncompleteAndExpression
	| expr orToken postLogicalOperatorWhitespace				# IncompleteOrExpression
	| expr commaToken											# CommaExpressionWrapper2
	| notToken postNotOperatorWhitespace						# IncompleteNotExpression
	| STAR postExpressionWhitespace								# AllExpression
	| value postExpressionWhitespace							# UnmatchedValue
	| commaToken												# CommaExpressionWrapper3;

// Allowed expressions within traversal contexts
traversalAllowedExpr:
	attributeName colonToken attributeValue (
		EQUAL attributeValue
	)? postAttributeValueWhitespace		# AttributeExpression
	| functionName parenthesizedExpr	# FunctionCallExpression
	| parenthesizedExpr					# TraversalAllowedParenthesizedExpression
	| incompleteExpr					# IncompleteExpression;

parenthesizedExpr:
	leftParenToken postLogicalOperatorWhitespace expr rightParenToken postExpressionWhitespace #
		ParenthesizedExpression;

incompleteExpr:
	attributeName colonToken attributeValue EQUAL attributeValueWhitespace #
		IncompleteAttributeExpressionMissingSecondValue
	| attributeName colonToken attributeValueWhitespace			# IncompleteAttributeExpressionMissingValue
	| functionName expressionLessParenthesizedExpr				# ExpressionlessFunctionExpression
	| functionName leftParenToken postLogicalOperatorWhitespace	#
		UnclosedExpressionlessFunctionExpression
	| functionName leftParenToken expr						# UnclosedFunctionExpression
	| leftParenToken postLogicalOperatorWhitespace expr		# UnclosedParenthesizedExpression
	| expressionLessParenthesizedExpr						# ExpressionlessParenthesizedExpressionWrapper
	| leftParenToken postLogicalOperatorWhitespace			# UnclosedExpressionlessParenthesizedExpression
	| DIGITS? PLUS postNeighborTraversalWhitespace			# IncompletePlusTraversalExpression
	| PLUS value postExpressionWhitespace					# IncompletePlusTraversalExpressionMissingValue
	| colonToken attributeValue postExpressionWhitespace	# IncompleteAttributeExpressionMissingKey;

expressionLessParenthesizedExpr:
	leftParenToken postLogicalOperatorWhitespace rightParenToken postExpressionWhitespace #
		ExpressionlessParenthesizedExpression;

upTraversalExpr:
	upTraversalToken postUpwardTraversalWhitespace # UpTraversal;

downTraversalExpr:
	downTraversalToken postDownwardTraversalWhitespace # DownTraversal;

upTraversalToken: DIGITS? PLUS;
downTraversalToken: PLUS DIGITS?;

// Attribute and function names (to be validated externally)
attributeName: IDENTIFIER;

attributeValue: value;

functionName: IDENTIFIER;

commaToken: COMMA postLogicalOperatorWhitespace;

orToken: OR;

andToken: AND;

notToken: NOT;

colonToken: COLON;

leftParenToken: LPAREN;

rightParenToken: RPAREN;

attributeValueWhitespace: WS*;

postAttributeValueWhitespace: WS*;

postExpressionWhitespace: WS*;

postNotOperatorWhitespace: WS*;

postLogicalOperatorWhitespace: WS*;

postNeighborTraversalWhitespace: WS*;

postUpwardTraversalWhitespace: WS*;

postDownwardTraversalWhitespace: WS*;

postDigitsWhitespace: WS*;

// Value can be a quoted string, unquoted string, or identifier
value:
	QUOTED_STRING						# QuotedStringValue
	| INCOMPLETE_LEFT_QUOTED_STRING		# IncompleteLeftQuotedStringValue
	| INCOMPLETE_RIGHT_QUOTED_STRING	# IncompleteRightQuotedStringValue
	| IDENTIFIER						# UnquotedStringValue
	| DIGITS							# DigitsValue;

// Tokens for operators and keywords
AND: 'and' | 'AND';
OR: 'or' | 'OR';
NOT: 'not' | 'NOT';

STAR: '*';
PLUS: '+';

DIGITS: [0-9]+;

COLON: ':';

LPAREN: '(';
RPAREN: ')';

// Tokens for strings
QUOTED_STRING: '"' (~["\\\r\n])* '"';
INCOMPLETE_LEFT_QUOTED_STRING: '"' (~["\\\r\n():=])*;
INCOMPLETE_RIGHT_QUOTED_STRING: (~["\\\r\n:()=])* '"';

EQUAL: '=';

// Identifiers (attributes and functions)
IDENTIFIER: [a-zA-Z0-9_*][a-zA-Z0-9_*/]*;

// Whitespace
WS: [ \t\r\n]+;

COMMA: ',';