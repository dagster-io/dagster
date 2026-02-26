import * as React from 'react';

import {Box} from '../Box';
import {Colors} from '../Color';
import {Tooltip} from '../Tooltip';

const SOLID_STYLES: React.CSSProperties = {
  background: Colors.backgroundDefault(),
  transform: 'translate(0,0)',
  border: `1px solid ${Colors.accentYellow()}`,
  color: Colors.textDefault(),
  fontSize: '12px',
  padding: 6,
};

const JOB_STYLES: React.CSSProperties = {
  background: Colors.backgroundDefault(),
  border: `1px solid ${Colors.borderDefault()}`,
  color: Colors.textDefault(),
  fontSize: '15px',
  padding: 3,
};

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Tooltip Overflow',
  component: Tooltip,
};

export const Default = () => {
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <p style={{color: Colors.textLight()}}>
        Use the <code>data-tooltip</code> attribute to expand truncated job, op names, etc. on
        hover. These are highly stylable via <code>data-tooltip-style</code> so they can look like
        boxes / nodes expanding in place to reveal their full text. There is no per-component render
        cost to these annotations so they can be used in cases when thousands of nodes are rendered.
        <br />
        <br />
        These tooltips automatically appear only when the content is truncated or when content
        contains a <code>…</code>
      </p>
      {['short_solid', 'long_solid_name_here'].map((name) => (
        <div
          key={name}
          data-tooltip={name}
          data-tooltip-style={JSON.stringify(SOLID_STYLES)}
          style={{
            width: '100px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            position: 'relative',
            ...SOLID_STYLES,
          }}
        >
          {name}
        </div>
      ))}

      <span
        data-tooltip="fetch_from_redshift_cloud_prod"
        data-tooltip-style={JSON.stringify(JOB_STYLES)}
        style={JOB_STYLES}
      >
        fetch_from_redshift…
      </span>
    </Box>
  );
};
