import {useEffect, useState} from 'react';

type Props = {
  placeholder: string;
  value: string;
  linter: (text: string) => {message: string}[];
  onChange: (value: string) => void;
};

// CodeMirror doesn't run in jsdom. This keeps the input's contract: the draft is local,
// Enter commits it, a new `value` replaces the draft, a draft that differs from `value` is
// marked uncommitted, and errors reflect `linter(value)`.
export const MockSelectionInput = ({placeholder, value, linter, onChange}: Props) => {
  const [draft, setDraft] = useState(value);
  const [firstError] = linter(value);

  useEffect(() => {
    setDraft(value);
  }, [value]);

  return (
    <>
      <input
        aria-label={placeholder}
        data-uncommitted={draft !== value}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            onChange(draft);
          }
        }}
      />
      <div role="alert">{firstError?.message}</div>
    </>
  );
};
