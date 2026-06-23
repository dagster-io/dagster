import {ComponentProps, useCallback} from 'react';

import {Box} from './Box';
import {RadioTag} from './RadioTag';
import styles from './css/RadioTags.module.css';

export interface RadioTagOption<T extends string> {
  value: T;
  label: string;
  icon?: ComponentProps<typeof RadioTag>['icon'];
  rightIcon?: ComponentProps<typeof RadioTag>['rightIcon'];
}

interface RadioTagsProps<T extends string> {
  name: string;
  options: RadioTagOption<T>[];
  value: T;
  onChange: (value: T) => void;
  'aria-label'?: string;
}

export const RadioTags = <T extends string>({
  name,
  options,
  value,
  onChange,
  'aria-label': ariaLabel,
}: RadioTagsProps<T>) => {
  return (
    <Box
      flex={{gap: 6, wrap: 'wrap', alignItems: 'center'}}
      role="radiogroup"
      aria-label={ariaLabel ?? name}
    >
      {options.map((option) => (
        <RadioTagItem
          key={option.value}
          name={name}
          option={option}
          selected={value === option.value}
          onChange={onChange}
        />
      ))}
    </Box>
  );
};

interface RadioTagItemProps<T extends string> {
  name: string;
  option: RadioTagOption<T>;
  selected: boolean;
  onChange: (value: T) => void;
}

const RadioTagItem = <T extends string>({
  name,
  option,
  selected,
  onChange,
}: RadioTagItemProps<T>) => {
  const handleChange = useCallback(() => {
    onChange(option.value);
  }, [onChange, option.value]);

  return (
    <label className={styles.label}>
      <input
        className={styles.hiddenInput}
        type="radio"
        name={name}
        value={option.value}
        checked={selected}
        onChange={handleChange}
      />
      <RadioTag icon={option.icon} rightIcon={option.rightIcon} selected={selected}>
        {option.label}
      </RadioTag>
    </label>
  );
};
