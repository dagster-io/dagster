import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import * as TestRenderer from 'react-test-renderer';

import {HighlightedCodeBlock} from '../HighlightedCodeBlock';

it('correctly renders keywords inside a comment', () => {
  const component = TestRenderer.create(
    <BrowserRouter>
      <HighlightedCodeBlock
        languages={['sql']}
        value={
          '-- this comment contains a dash - do not highlight if drop table\n' +
          'select * from q2_on_time_data\n' +
          "where origin = 'SFO'"
        }
        style={{
          height: 510,
          margin: 0,
          overflow: 'scroll',
          fontSize: '0.9em',
        }}
      />
    </BrowserRouter>,
  );
  expect(component.toJSON()).toMatchSnapshot();
});
