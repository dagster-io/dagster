import * as React from 'react';
import {act, create, ReactTestRenderer} from 'react-test-renderer';

import {useDocumentTitle} from 'src/hooks/useDocumentTitle';

describe('useDocumentTitle', () => {
  const Test = (props: {children?: React.ReactNode; title: string}) => {
    const {children, title} = props;
    useDocumentTitle(title);
    return <div>{children}</div>;
  };

  it('sets the document title', () => {
    act(() => {
      create(<Test title="foo" />);
    });
    expect(document.title).toBe('foo');
  });

  it('allows child to set title, and restores original title on child unmount', () => {
    let root: ReactTestRenderer;
    act(() => {
      root = create(<Test title="foo" />);
    });
    expect(document.title).toBe('foo');
    act(() => {
      root.update(
        <Test title="foo">
          <Test title="bar" />
        </Test>,
      );
    });
    expect(document.title).toBe('bar');
    act(() => {
      root.update(<Test title="foo" />);
    });
    expect(document.title).toBe('foo');
  });

  it('updates title when swapping in or unmounting another child', () => {
    let root: ReactTestRenderer;
    act(() => {
      root = create(<Test title="foo" />);
    });
    expect(document.title).toBe('foo');
    act(() => {
      root.update(
        <Test title="foo">
          <Test title="bar" />
        </Test>,
      );
    });
    expect(document.title).toBe('bar');
    act(() => {
      root.update(
        <Test title="foo">
          <Test title="baz" />
        </Test>,
      );
    });
    expect(document.title).toBe('baz');
    act(() => {
      root.update(<Test title="foo" />);
    });
    expect(document.title).toBe('foo');
  });
});
