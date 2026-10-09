import {renderHook} from '@testing-library/react';

import {useRestoreFocus} from '../useRestoreFocus';

const mountButton = () => {
  const button = document.createElement('button');
  document.body.appendChild(button);
  return button;
};

describe('useRestoreFocus', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('returns focus to the remembered trigger', () => {
    const trigger = mountButton();
    const fallback = mountButton();
    const {result} = renderHook(() => useRestoreFocus(() => fallback));

    result.current.rememberTrigger(trigger);
    result.current.restoreFocus();

    expect(trigger).toHaveFocus();
  });

  it('falls back when the trigger has left the document', () => {
    const trigger = mountButton();
    const fallback = mountButton();
    const {result} = renderHook(() => useRestoreFocus(() => fallback));

    result.current.rememberTrigger(trigger);
    trigger.remove();
    result.current.restoreFocus();

    expect(fallback).toHaveFocus();
  });

  it('leaves focus alone when nothing was remembered', () => {
    const fallback = mountButton();
    const other = mountButton();
    other.focus();
    const {result} = renderHook(() => useRestoreFocus(() => fallback));

    result.current.restoreFocus();

    expect(other).toHaveFocus();
  });

  it('forgets the trigger once it has been restored', () => {
    const trigger = mountButton();
    const other = mountButton();
    const {result} = renderHook(() => useRestoreFocus(() => null));

    result.current.rememberTrigger(trigger);
    result.current.restoreFocus();
    other.focus();
    result.current.restoreFocus();

    expect(other).toHaveFocus();
  });
});
