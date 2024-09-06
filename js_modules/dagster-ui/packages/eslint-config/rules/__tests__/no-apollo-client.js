/* eslint-disable */
const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');

const ruleTester = new ESLintUtils.RuleTester({
  parser: '@typescript-eslint/parser',
});

const rule = require('../no-apollo-client');

ruleTester.run('rule', rule, {
  valid: [
    `
      import {useQuery} from '../../apollo-client';
    `,
  ],
  invalid: [
    {
      code: `
        import {useQuery} from '@apollo/client';
      `,
      output: `
        import {useQuery} from '@dagster-io/ui-core/apollo-client';
      `,
      errors: [
        {
          type: AST_NODE_TYPES.ImportDeclaration,
          messageId: 'useWrappedApolloClient',
        },
      ],
    },
  ],
});
