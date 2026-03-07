import React from 'react';

import {makeSVGPortable} from './makeSVGPortable';

export const SVGExporter = ({
  element,
  onDone,
}: {
  element: React.RefObject<HTMLDivElement>;
  onDone: () => void;
}) => {
  React.useLayoutEffect(() => {
    const ready = async () => {
      // Find the rendered SVG node
      const svgOriginal = element.current?.querySelector('svg') as SVGElement;
      if (!svgOriginal) {
        onDone();
        return;
      }

      // Copy the node rendered by React, attach it and inline all the styles
      // (this mutates the DOM so it must be a copy of the element!)
      const svg = svgOriginal.cloneNode(true) as SVGElement;
      svgOriginal.parentElement?.appendChild(svg);
      await makeSVGPortable(svg);
      const text = new XMLSerializer().serializeToString(svg);
      svg.remove();

      // Trigger a file download
      const blob = new Blob([text], {type: 'image/svg+xml'});
      const a = document.createElement('a');
      a.setAttribute(
        'download',
        `${document.title.replace(/[: \/]/g, '_').replace(/__+/g, '_')}.svg`,
      );
      a.setAttribute('href', URL.createObjectURL(blob));
      a.click();

      onDone();
    };
    void ready();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <></>;
};
