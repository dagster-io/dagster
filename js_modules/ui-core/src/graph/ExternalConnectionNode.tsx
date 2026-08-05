import {Colors} from '@dagster-io/ui-components';
import {LinkVertical as Link} from '@visx/shape';

import {Edge} from './OpEdges';
import {SVGMonospaceText} from './SVGComponents';
import {IPoint, isHighlighted} from './common';
import styles from './css/ExternalConnectionNode.module.css';

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

export const ExternalConnectionNode = ({
  layout,
  target,
  edges,
  label,
  labelAttachment,
  minified,
  highlightedEdges,
  onHighlightEdges,
  onDoubleClickLabel,
}: ExternalConnectionNodeProps) => {
  const textProps = {width: 0, size: minified ? 24 : 12, text: label};
  const textSize = SVGMonospaceText.intrinsicSizeForProps(textProps);
  const highlighted = edges.some((e) => isHighlighted(highlightedEdges, e));
  const color = highlighted ? Colors.lineageEdgeHighlighted() : Colors.lineageEdge();

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
      <rect
        className={styles.backingRect}
        {...textSize}
        {...textOrigin}
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={(e) => {
          e.stopPropagation();
          onDoubleClickLabel();
        }}
      />
      <ellipse cx={layout.x} cy={layout.y} rx={7} ry={7} fill={color} />
      <SVGMonospaceText {...textProps} {...textSize} {...textOrigin} fill={Colors.textDefault()} />
      <Link style={{stroke: color, strokeWidth: 6, fill: 'none'}} data={{source: layout, target}} />
    </g>
  );
};
