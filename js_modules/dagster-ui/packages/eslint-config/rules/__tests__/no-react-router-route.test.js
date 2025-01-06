/* eslint-disable */
const {RuleTester} = require('@typescript-eslint/rule-tester');

const ruleTester = new RuleTester();

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
          type: 'ImportDeclaration',
          messageId: 'useDagsterRoute',
        },
      ],
    },
  ],
});
