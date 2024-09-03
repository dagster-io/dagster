/* eslint-disable */
const {ESLintUtils, AST_NODE_TYPES} = require('@typescript-eslint/utils');

const ruleTester = new ESLintUtils.RuleTester({
  parser: '@typescript-eslint/parser',
});

const rule = require('../no-react-router-route');

ruleTester.run('rule', rule, {
  valid: [
    `
      import {Redirect, Switch} from 'react-router-dom';

      import {Route} from './Route';
    `,
  ],
  invalid: [
    {
      code: `
import {Redirect, Route, Switch} from 'react-router-dom';
      `,
      output: `
import { Route } from '@dagster-io/ui-core/app/Route';
import {Redirect, Switch} from 'react-router-dom';
      `,
      errors: [
        {
          type: AST_NODE_TYPES.ImportDeclaration,
          messageId: 'useDagsterRoute',
        },
      ],
    },
  ],
});
