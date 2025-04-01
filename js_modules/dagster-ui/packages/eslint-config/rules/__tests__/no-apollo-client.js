/* eslint-disable */
const {RuleTester} = require('@typescript-eslint/rule-tester');

const ruleTester = new RuleTester();

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
          type: 'ImportDeclaration',
          messageId: 'useWrappedApolloClient',
        },
      ],
    },
  ],
});
