import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {unmountComponentAtNode} from 'react-dom';
import {act} from 'react-dom/test-utils';

import {TokenizingField} from './TokenizingField';

// https://github.com/jsdom/jsdom/issues/317
(global as any).document.createRange = () => ({
  setStart: () => {},
  setEnd: () => {},
  commonAncestorContainer: {
    nodeName: 'BODY',
    ownerDocument: document,
  },
});

// https://stackoverflow.com/questions/23892547/what-is-the-best-way-to-trigger-onchange-event-in-react-js
const setValue = (node: HTMLInputElement, value: string) => {
  Object.getOwnPropertyDescriptor((node as any).__proto__, 'value')!.set!.call(node, value);
  node.dispatchEvent(new Event('change', {bubbles: true}));
};

const suggestions = [
  {
    token: 'pipeline',
    values: () => ['airline_demo_ingest', 'airline_demo_warehouse', 'composition'],
  },
  {
    token: 'status',
    values: () => ['QUEUED', 'NOT_STARTED', 'STARTED', 'SUCCESS', 'FAILURE', 'MANAGED'],
  },
];

let container: HTMLElement;

beforeEach(() => {
  // setup a DOM element as a render target
  container = document.createElement('div');
  // container *must* be attached to document so events work correctly.
  document.body.appendChild(container);
});

afterEach(() => {
  // cleanup on exiting
  unmountComponentAtNode(container);
  container.remove();
});

function expectOptions(expected: string[]) {
  const actual = Array.from(document.documentElement.querySelectorAll('.bp3-menu-item')).map(
    (el) => el.textContent,
  );

  expect(actual).toEqual(expected);
}

// These tests render into a real DOM node so we can test interactions

it('shows available autocompletion options when clicked', () => {
  const onChange = jest.fn();
  ReactDOM.render(
    <TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />,
    container,
  );
  act(() => {
    container.querySelector('input')!.focus();
  });

  expectOptions(['pipeline:', 'status:']);
});

it('filters properly when typing `pipeline` prefix', () => {
  const onChange = jest.fn();
  ReactDOM.render(
    <TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />,
    container,
  );
  const inputEl = container.querySelector('input')!;
  act(() => {
    inputEl.focus();
    setValue(inputEl, 'pipeli');
  });
  expectOptions([
    'pipeline:',
    'pipeline:airline_demo_ingest',
    'pipeline:airline_demo_warehouse',
    'pipeline:composition',
  ]);
  act(() => {
    setValue(inputEl, 'pipeline');
  });
  expectOptions([
    'pipeline:',
    'pipeline:airline_demo_ingest',
    'pipeline:airline_demo_warehouse',
    'pipeline:composition',
  ]);
  act(() => {
    setValue(inputEl, 'pipeline:');
  });
  expectOptions([
    'pipeline:airline_demo_ingest',
    'pipeline:airline_demo_warehouse',
    'pipeline:composition',
  ]);
});

it('filters properly when typing a value without the preceding token', () => {
  const onChange = jest.fn();
  ReactDOM.render(
    <TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />,
    container,
  );
  const inputEl = container.querySelector('input')!;
  act(() => {
    inputEl.focus();
    setValue(inputEl, 'airline');
    inputEl.dispatchEvent(new Event('change', {bubbles: true}));
  });
  expectOptions(['pipeline:airline_demo_ingest', 'pipeline:airline_demo_warehouse']);
});
