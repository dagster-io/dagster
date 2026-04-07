import {ComponentProps, useCallback} from 'react';

import {Box} from './Box';
import {RadioTag} from './RadioTag';
import styles from './css/RadioTags.module.css';

interface RadioTagOption {
  value: string;
  label: string;
  icon?: ComponentProps<typeof RadioTag>['icon'];
  rightIcon?: ComponentProps<typeof RadioTag>['rightIcon'];
}

interface RadioTagsProps {
  name: string;
  options: RadioTagOption[];
  value: string;
  onChange: (value: string) => void;
  'aria-label'?: string;
}

export const RadioTags = ({
  name,
  options,
  value,
  onChange,
  'aria-label': ariaLabel,
}: RadioTagsProps) => {
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

interface RadioTagItemProps {
  name: string;
  option: RadioTagOption;
  selected: boolean;
  onChange: (value: string) => void;
}

const RadioTagItem = ({name, option, selected, onChange}: RadioTagItemProps) => {
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
