import {Meta} from '@storybook/react';
import faker from 'faker';
import * as React from 'react';

import {Box} from '../Box';
import {Colors} from '../Colors';
import {Icon} from '../Icon';
import {MiddleTruncate} from '../MiddleTruncate';
import {Slider} from '../Slider';
import {Tag} from '../Tag';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'MiddleTruncate',
  component: MiddleTruncate,
} as Meta;

export const Simple = () => {
  const sizer = React.useRef<HTMLDivElement>(null);
  const [controlledWidth, setControlledWidth] = React.useState(400);

  const sentences = React.useMemo(() => {
    return new Array(30).fill(null).map(() => faker.random.words(20));
  }, []);

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
        {sentences.map((sentence) => (
          <div key={sentence}>
            <MiddleTruncate text={sentence} />
          </div>
        ))}
        <MiddleTruncate text="Hello world" />
      </div>
    </>
  );
};

export const FlexboxContainerUsage = () => {
  return (
    <Box>
      <em style={{display: 'block', marginBottom: 10}}>
        Note: When testing this in Firefox, view it on both a Retina and non-Retina display. Some
        rounding issues only seem to happen on Retina displays.
      </em>
      {[
        'asset_0',
        'asset1',
        'example',
        'test1234',
        'example_1',
        'helloworld',
        'example_12',
        'example_123',
        'otherstring',
        'example_1234',
        'a_source_asset',
        'variable_width',
        'yoyo_multidim',
        'yoyo_multidim_other_order',
        'activity_daily_stats',
        'asset_that_supports_partition_ranges',
      ].map((text) => (
        <Box key={text} style={{maxWidth: '100%'}} flex={{direction: 'row', gap: 8}}>
          <Box>
            <Icon name="asset_non_sda" />
          </Box>
          <a style={{overflow: 'hidden'}} href="#/">
            <MiddleTruncate text={text} />
          </a>
        </Box>
      ))}
    </Box>
  );
};
export const TagUsage = () => {
  return (
    <Tag icon="job">
      <span>
        Job in{' '}
        <Box
          flex={{display: 'inline-flex', direction: 'row', alignItems: 'center'}}
          style={{maxWidth: 100}}
        >
          <MiddleTruncate text="repo@longrepolocation.py" />
        </Box>
      </span>
    </Tag>
  );
};

export const Containers = () => {
  const sizer = React.useRef<HTMLDivElement>(null);
  const [controlledWidth, setControlledWidth] = React.useState(400);

  const LONG_TEXT =
    'Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal.';
  const SHORT_TEXT = 'Hello world';
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
        <Box flex={{direction: 'row', gap: 24, alignItems: 'center'}} margin={{vertical: 12}}>
          <Box
            flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}
            background={Colors.Gray100}
            padding={12}
            style={{overflow: 'hidden'}}
          >
            <div style={{width: '100%'}}>
              <MiddleTruncate text={LONG_TEXT} />
            </div>
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{maxWidth: '100px'}}
            >
              <Icon name="account_circle" />
              <MiddleTruncate text={LONG_TEXT} />
            </Box>
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{maxWidth: '300px'}}
            >
              <Icon name="account_circle" />
              <MiddleTruncate text={LONG_TEXT} />
            </Box>
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{width: '100%'}}
            >
              <Icon name="account_circle" />
              <div style={{flex: 1, overflow: 'hidden'}}>
                <MiddleTruncate text={LONG_TEXT} />
              </div>
            </Box>
            <Box flex={{direction: 'row', gap: 4}} background={Colors.Blue100} padding={4}>
              <Icon name="account_circle" />
              <MiddleTruncate text={LONG_TEXT} />
            </Box>
          </Box>
        </Box>
        <Box margin={{bottom: 12}}>
          <Box
            flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}
            background={Colors.Gray100}
            padding={12}
            style={{overflow: 'hidden'}}
          >
            <MiddleTruncate text={SHORT_TEXT} />
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{maxWidth: '100px'}}
            >
              <Icon name="account_circle" />
              <MiddleTruncate text={SHORT_TEXT} />
            </Box>
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{maxWidth: '60px'}}
            >
              <Icon name="account_circle" />
              <MiddleTruncate text={SHORT_TEXT} />
            </Box>
            <Box
              flex={{direction: 'row', gap: 4}}
              background={Colors.Blue100}
              padding={4}
              style={{maxWidth: '100%'}}
            >
              <Icon name="account_circle" />
              <MiddleTruncate text={SHORT_TEXT} />
            </Box>
            <Box flex={{direction: 'row', gap: 4}} background={Colors.Blue100} padding={4}>
              <Icon name="account_circle" />
              <MiddleTruncate text={SHORT_TEXT} />
            </Box>
          </Box>
        </Box>
      </div>
    </>
  );
};
