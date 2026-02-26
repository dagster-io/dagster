grammar AutomationSelection;

start: expr EOF;

// Root rule for parsing expressions
expr:
	traversalAllowedExpr								# TraversalAllowedExpression
	| NOT expr											# NotExpression
	| expr AND expr										# AndExpression
	| expr OR expr										# OrExpression
	| STAR												# AllExpression;

// Allowed expressions for traversals
traversalAllowedExpr:
	attributeExpr						# AttributeExpression
	| LPAREN expr RPAREN				# ParenthesizedExpression;

// Attribute expressions for specific attributes
attributeExpr:
	NAME COLON keyValue # NameExpr
    | TAG COLON value (EQUAL value)? # TagExpr
    | TYPE COLON value # TypeExpr
    | STATUS COLON value # StatusExpr
	| CODE_LOCATION COLON value # CodeLocationExpr;

// Value can be a quoted or unquoted string
value: QUOTED_STRING | UNQUOTED_STRING | NULL_STRING;
keyValue:
	QUOTED_STRING
	| UNQUOTED_STRING
	| UNQUOTED_WILDCARD_STRING;

// Tokens for operators and keywords
AND: 'and' | 'AND';
OR: 'or' | 'OR';
NOT: 'not' | 'NOT';

EQUAL: '=';

COLON: ':';

STAR: '*';

LPAREN: '(';
RPAREN: ')';

// Tokens for attributes
NAME: 'name';
CODE_LOCATION: 'code_location';
TAG: 'tag';
STATUS: 'status';
TYPE: 'type';

// Tokens for strings
QUOTED_STRING: '"' (~["\\\r\n])* '"';
UNQUOTED_STRING: [a-zA-Z_][@a-zA-Z0-9_]*;
UNQUOTED_WILDCARD_STRING: [a-zA-Z_*][@a-zA-Z0-9_*]*;
NULL_STRING: '<null>';

// Whitespace
WS: [ \t\r\n]+ -> skip;