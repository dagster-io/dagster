grammar OpSelection;

start: expr EOF;

// Root rule for parsing expressions
expr
    : traversalAllowedExpr                         # TraversalAllowedExpression
    | traversal traversalAllowedExpr traversal     # UpAndDownTraversalExpression
    | traversal traversalAllowedExpr               # UpTraversalExpression
    | traversalAllowedExpr traversal               # DownTraversalExpression
    | NOT expr                                     # NotExpression
    | expr AND expr                                # AndExpression
    | expr OR expr                                 # OrExpression
    | STAR                                         # AllExpression
    ;

// Allowed expressions for traversals
traversalAllowedExpr
    : attributeExpr                                # AttributeExpression
    | LPAREN expr RPAREN                           # ParenthesizedExpression
    ;

// Traversal operators
traversal
    : STAR
    | PLUS+
    ;

// Attribute expressions for specific attributes
attributeExpr
    : NAME COLON value                              # NameExpr
    | NAME_SUBSTRING COLON value                    # NameSubstringExpr
    ;

// Value can be a quoted or unquoted string
value
    : QUOTED_STRING
    | UNQUOTED_STRING
    ;

// Tokens for operators and keywords
AND : 'and';
OR : 'or';
NOT : 'not';

STAR : '*';
PLUS : '+';

COLON : ':';

LPAREN : '(';
RPAREN : ')';

// Tokens for attributes
NAME : 'name';
NAME_SUBSTRING : 'name_substring';

// Tokens for strings
QUOTED_STRING : '"' (~["\\\r\n])* '"' ;
UNQUOTED_STRING : [a-zA-Z_][a-zA-Z0-9_]*;

// Whitespace
WS : [ \t\r\n]+ -> skip ;