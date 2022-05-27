const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');


const ruleTester = new ESLintUtils.RuleTester({
  parser: '@typescript-eslint/parser',
});

jest.mock('fs');
const fs = require('fs');
const {rule} = require('../missing-graphql-variables-type');

fs.readFileSync = (path) => {
  if (path.includes('WithVariables')) {
    return `
      export interface SomeQuery {}
      export interface SomeQueryVariables {}
    `
  } else {
    return `
      export interface SomeQuery {}
    `
  }
}

ruleTester.run('missing-graphql-variables', rule, {
  valid: [
    `
      import { SomeQuery, SomeQueryVariables } from '../SomeQueryWithVariables';
      useQuery<SomeQuery, SomeQueryVariables>();
    `,
    `
      import { SomeQuery } from '../SomeQueryWithOutVariables';
      useQuery<SomeQuery>();
    `,
  ],
  invalid: [
    {
      code: `
      import { SomeQuery } from '../SomeQueryWithVariables';
      useQuery<SomeQuery>();
    `,
      errors: [{type: AST_NODE_TYPES.CallExpression, messageId: 'missing-graphql-variables-type'}],
    },
  ],
});
