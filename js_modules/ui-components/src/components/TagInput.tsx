import clsx from 'clsx';
import * as React from 'react';

import {Icon} from './Icon';
import {Menu, MenuItem} from './Menu';
import {Popover} from './Popover';
import styles from './css/TokenizingField.module.css';

export interface TagInputTagProps {
  intent?: 'danger' | 'success' | 'warning';
}

interface TagInputProps {
  values: string[];
  onChange?: (values: string[]) => void;
  onInputChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  showAddMenu?: boolean;
  placeholder?: string;
  tagProps?: TagInputTagProps | ((value: string, index: number) => TagInputTagProps);
  className?: string;
  maxWidth?: string;
}

const intentToClass = (intent?: string) => {
  switch (intent) {
    case 'danger':
      return styles.tagDanger;
    case 'success':
      return styles.tagSuccess;
    case 'warning':
      return styles.tagWarning;
    default:
      return styles.tagDefault;
  }
};

export const TagInput = ({
  maxWidth,
  className,
  values,
  onChange,
  onInputChange,
  showAddMenu,
  placeholder,
  tagProps,
}: TagInputProps) => {
  const [inputValue, setInputValue] = React.useState('');
  const [focused, setFocused] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const addValues = (texts: string[]) => {
    const trimmed = texts.map((t) => t.trim()).filter((t) => t !== '' && !values.includes(t));
    if (trimmed.length > 0 && onChange) {
      onChange([...values, ...trimmed]);
      setInputValue('');
    }
  };

  const getTagProps = (value: string, idx: number): TagInputTagProps => {
    if (typeof tagProps === 'function') {
      return tagProps(value, idx);
    }
    return tagProps || {};
  };

  const handleInputChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(e.currentTarget.value);
      onInputChange?.(e);
    },
    [onInputChange],
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (inputValue.trim()) {
        e.preventDefault();
        addValues([inputValue.trim()]);
      }
    }
    if (e.key === 'Backspace' && inputValue === '' && values.length > 0) {
      onChange?.(values.slice(0, -1));
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text');
    const items = pasted
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (items.length > 0) {
      addValues(items);
    }
  };

  const handleFocus = React.useCallback(() => setFocused(true), []);

  const handleBlur = () => {
    setFocused(false);
    if (inputValue.trim()) {
      addValues([inputValue.trim()]);
    }
  };

  const handleAddMenuMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (e.button !== 0 || e.metaKey || e.ctrlKey) {
      return;
    }
    e.stopPropagation();
    addValues([inputValue.trim()]);
  };

  const container = (
    <div
      className={clsx(
        styles.styledTagInput,
        maxWidth === '100%' && styles.fullWidth,
        className,
        focused && styles.active,
      )}
      onClick={() => inputRef.current?.focus()}
    >
      <div className={styles.tagInputValues}>
        {values.map((v, idx) => {
          const props = getTagProps(v, idx);
          return (
            <span key={`${v}-${idx}`} className={clsx(styles.tag, intentToClass(props.intent))}>
              <span className={styles.tagText}>{v}</span>
              <button
                className={styles.tagRemove}
                onClick={(e) => {
                  e.stopPropagation();
                  if (onChange) {
                    const next = [...values];
                    next.splice(idx, 1);
                    onChange(next);
                  }
                }}
                tabIndex={-1}
                type="button"
                aria-label="Remove"
              >
                <Icon name="close" size={12} />
              </button>
            </span>
          );
        })}
        <input
          ref={inputRef}
          className={clsx(styles.input, values.length === 0 && styles.inputFirst)}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
        />
      </div>
    </div>
  );

  if (!showAddMenu) {
    return container;
  }

  return (
    <Popover
      isOpen={focused && inputValue.trim().length > 0}
      position="bottom-left"
      content={
        <Menu>
          <MenuItem
            text={
              <span>
                Add <strong>{inputValue.trim()}</strong>
              </span>
            }
            active
            onMouseDown={handleAddMenuMouseDown}
          />
        </Menu>
      }
    >
      {container}
    </Popover>
  );
};
