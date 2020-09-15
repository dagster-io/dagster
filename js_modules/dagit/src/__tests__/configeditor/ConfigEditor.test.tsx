import * as React from 'react';
import * as TestRenderer from 'react-test-renderer';
import {BrowserRouter} from 'react-router-dom';

import {ConfigEditor} from '../../configeditor/ConfigEditor';

it('renders a codemirror', () => {
  // This test does very little, unfortunately, because JSDOM doesn't really support the APIs that
  // CodeMirror relies on. Placeholder. We would like to be able to make assertions about formatting
  // with this snapshot, but we can't.
  // https://github.com/jsdom/jsdom/issues/317
  // https://stackoverflow.com/questions/21572682/createtextrange-is-not-working-in-chrome/46424247#46424247
  const global_: any = global;
  global_.document.body.createTextRange = () => {
    return {
      setEnd: () => {},
      setStart: () => {},
      getBoundingClientRect: () => {},
      getClientRects: () => [],
    };
  };

  const configEditorComponent = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditor
        checkConfig={async () => ({
          isValid: true,
        })}
        onConfigChange={() => null}
        onHelpContextChange={() => null}
        readOnly={true}
        configCode={"solids:\n  foo:\n    config:\n      baz:\n        ['s3://foo', 'bar']\n"}
        showWhitespace={true}
      />
    </BrowserRouter>,
  );
  expect(configEditorComponent.toJSON()).toMatchSnapshot();
});
