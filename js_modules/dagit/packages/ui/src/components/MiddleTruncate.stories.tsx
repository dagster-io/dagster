import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {MiddleTruncate} from './MiddleTruncate';
import {Slider} from './Slider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'MiddleTruncate',
  component: MiddleTruncate,
} as Meta;

export const Simple = () => {
  const sizer = React.useRef<HTMLDivElement>(null);
  const [width, setWidth] = React.useState<number | null>(null);
  const [controlledWidth, setControlledWidth] = React.useState(400);

  const sentences = React.useMemo(() => {
    return new Array(30).fill(null).map(() => faker.random.words(20));
  }, []);

  React.useEffect(() => {
    const width = sizer.current?.getBoundingClientRect().width;
    if (width) {
      setWidth(width);
    }
  }, [controlledWidth]);

  return (
    <>
      <Slider
        min={200}
        max={600}
        stepSize={10}
        value={controlledWidth}
        labelRenderer={false}
        onChange={(value) => setControlledWidth(value)}
      />
      <div ref={sizer} style={{width: controlledWidth}}>
        {width
          ? sentences.map((sentence) => (
              <div key={sentence}>
                <MiddleTruncate text={sentence} />
              </div>
            ))
          : null}
        {width ? <MiddleTruncate text="Hello world" /> : null}
      </div>
    </>
  );
};
