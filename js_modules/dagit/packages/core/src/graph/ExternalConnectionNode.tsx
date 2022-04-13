import {Colors} from '@dagster-io/ui';
import {LinkVertical as Link} from '@vx/shape';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Edge} from './OpEdges';
import {SVGMonospaceText} from './SVGComponents';
import {IPoint, isHighlighted} from './common';

interface ExternalConnectionNodeProps {
  layout: IPoint;
  target: IPoint;
  labelAttachment: 'top' | 'bottom';
  label: string;
  minified: boolean;

  // Passed through from Solid props
  edges: Edge[];
  highlightedEdges: Edge[];
  onHighlightEdges: (edges: Edge[]) => void;
  onDoubleClickLabel: () => void;
}

export const ExternalConnectionNode: React.FC<ExternalConnectionNodeProps> = ({
  layout,
  target,
  edges,
  label,
  labelAttachment,
  minified,
  highlightedEdges,
  onHighlightEdges,
  onDoubleClickLabel,
}) => {
  const textProps = {width: 0, size: minified ? 24 : 12, text: label};
  const textSize = SVGMonospaceText.intrinsicSizeForProps(textProps);
  const highlighted = edges.some((e) => isHighlighted(highlightedEdges, e));
  const color = highlighted ? '#555' : '#C7CBCD';

  // https://github.com/dagster-io/dagster/issues/1504
  if (!layout) {
    return null;
  }

  const textOrigin = {
    x: layout.x - textSize.width / 2,
    y: layout.y + (labelAttachment === 'top' ? -10 - textSize.height : 10),
  };

  return (
    <g onMouseEnter={() => onHighlightEdges(edges)} onMouseLeave={() => onHighlightEdges([])}>
      <BackingRect
        {...textSize}
        {...textOrigin}
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={(e) => {
          e.stopPropagation();
          onDoubleClickLabel();
        }}
      />
      <ellipse cx={layout.x} cy={layout.y} rx={7} ry={7} fill={color} />
      <SVGMonospaceText {...textProps} {...textSize} {...textOrigin} />
      <Link style={{stroke: color, strokeWidth: 6, fill: 'none'}} data={{source: layout, target}} />
    </g>
  );
};

const BackingRect = styled('rect')`
  stroke-width: 10px;
  fill: ${Colors.Gray100};
  stroke: ${Colors.Gray100};
  &:hover {
    fill: ${Colors.Gray200};
    stroke: ${Colors.Gray200};
  }
`;
