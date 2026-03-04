/* eslint-disable */
const {RuleTester} = require('@typescript-eslint/rule-tester');

const ruleTester = new RuleTester();

jest.mock('fs');
// @ts-expect-error - using require because this package isn't setup for import declarations
const fs = require('fs');

// @ts-expect-error - using require because this package isn't setup for import declarations
const rule = require('../missing-graphql-variables-type');

fs.readFileSync = (path) => {
  const api = path.includes('Query')
    ? 'Query'
    : path.includes('Mutation')
      ? 'Mutation'
      : 'Subscription';
  if (path.includes('WithVariables')) {
    return `
      export type Some${api} {}
      export type Some${api}Variables {}
    `;
  } else {
    return `
      export type Some${api} {}
    `;
  }
};

ruleTester.run('missing-graphql-variables', rule, {
  valid: [
    `
      import { SomeQuery, SomeQueryVariables } from '../SomeQueryWithVariables';
      useQuery<SomeQuery, SomeQueryVariables>();
    `,
    `
      import { SomeMutation, SomeMutationVariables } from '../SomeMutationWithVariables';
      useMutation<SomeMutation, SomeMutationVariables>();
    `,
    `
      import { SomeSubscription, SomeSubscriptionVariables } from '../SomeSubscriptionWithVariables';
      useSubscription<SomeSubscription, SomeSubscriptionVariables>();
    `,
  ],
  invalid: [
    {
      code: `
        import { SomeQuery } from '../SomeQueryWithVariables';
        useQuery<SomeQuery>();
      `,
      output: `
        import { SomeQuery, SomeQueryVariables } from '../SomeQueryWithVariables';
        useQuery<SomeQuery, SomeQueryVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
    {
      code: `
        import { SomeQuery, SomeQueryVariables } from '../SomeQueryWithVariables';
        useQuery<SomeQuery>();
      `,
      output: `
        import { SomeQuery, SomeQueryVariables } from '../SomeQueryWithVariables';
        useQuery<SomeQuery, SomeQueryVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
    {
      code: `
        import { SomeMutation } from '../SomeMutationWithVariables';
        useMutation<SomeMutation>();
      `,
      output: `
        import { SomeMutation, SomeMutationVariables } from '../SomeMutationWithVariables';
        useMutation<SomeMutation, SomeMutationVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
    {
      code: `
        import { SomeMutation, SomeMutationVariables } from '../SomeMutationWithVariables';
        useMutation<SomeMutation>();
      `,
      output: `
        import { SomeMutation, SomeMutationVariables } from '../SomeMutationWithVariables';
        useMutation<SomeMutation, SomeMutationVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
    {
      code: `
        import { SomeSubscription } from '../SomeSubscriptionWithVariables';
        useSubscription<SomeSubscription>();
      `,
      output: `
        import { SomeSubscription, SomeSubscriptionVariables } from '../SomeSubscriptionWithVariables';
        useSubscription<SomeSubscription, SomeSubscriptionVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
    {
      code: `
        import { SomeSubscription, SomeSubscriptionVariables } from '../SomeSubscriptionWithVariables';
        useSubscription<SomeSubscription>();
      `,
      output: `
        import { SomeSubscription, SomeSubscriptionVariables } from '../SomeSubscriptionWithVariables';
        useSubscription<SomeSubscription, SomeSubscriptionVariables>();
      `,
      errors: [
        {
          type: 'CallExpression',
          messageId: 'missing-graphql-variables-type',
        },
      ],
    },
  ],
});
