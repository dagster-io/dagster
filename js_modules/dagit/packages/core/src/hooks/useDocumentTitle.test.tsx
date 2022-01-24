import {render} from '@testing-library/react';
import * as React from 'react';

import {useDocumentTitle} from './useDocumentTitle';

describe('useDocumentTitle', () => {
  const Test: React.FC<{title: string}> = (props) => {
    const {children, title} = props;
    useDocumentTitle(title);
    return <div>{children}</div>;
  };

  it('sets the document title', () => {
    render(<Test title="foo" />);
    expect(document.title).toBe('foo');
  });

  it('allows child to set title, and restores original title on child unmount', () => {
    const {rerender} = render(<Test title="foo" />);
    expect(document.title).toBe('foo');

    rerender(
      <Test title="foo">
        <Test title="bar" />
      </Test>,
    );

    expect(document.title).toBe('bar');

    rerender(<Test title="foo" />);
    expect(document.title).toBe('foo');
  });

  it('updates title when swapping in or unmounting another child', () => {
    const {rerender} = render(<Test title="foo" />);
    expect(document.title).toBe('foo');

    rerender(
      <Test title="foo">
        <Test title="bar" />
      </Test>,
    );
    expect(document.title).toBe('bar');

    rerender(
      <Test title="foo">
        <Test title="baz" />
      </Test>,
    );
    expect(document.title).toBe('baz');

    rerender(<Test title="foo" />);
    expect(document.title).toBe('foo');
  });
});
