const USED_ATTRIBUTES = [
  '-moz-osx-font-smoothing',
  'align-items',
  'align-self',
  'animation',
  'background',
  'border',
  'box-shadow',
  'box-sizing',
  'color',
  'column-gap',
  'display',
  'flex',
  'font',
  'fill',
  'gap',
  'height',
  'justify-content',
  'left',
  'letter-spacing',
  'line-height',
  'margin',
  'mask-image',
  '-webkit-mask-image',
  'mask-size',
  '-webkit-mask-size',
  'min-height',
  'min-width',
  'object-fit',
  'opacity',
  'overflow',
  'padding',
  'position',
  'row-gap',
  'stroke',
  'text-align',
  'text-decoration',
  'text-overflow',
  'text-transform',
  'top',
  'transform',
  'white-space',
  'width',
];

const attributeURLToBase64Map: {[attrURL: string]: string} = {};

async function makeAttributeValuePortable(attrValue: string) {
  // If the attribute value references a url(http:...), fetch it and convert
  // it to an inline base64 data url. (This replaces our dependency on icon SVGs)
  if (attrValue.startsWith('url(')) {
    const match = attrValue.match(/url\(['"]?(http[^'"]+)['"]?\)/);
    if (match) {
      const url = match[1];
      if (!attributeURLToBase64Map[url]) {
        const data = await fetch(url);
        attributeURLToBase64Map[url] = btoa(await data.text());
      }
      attrValue = attrValue.replace(
        url,
        `data:image/svg+xml;base64,${attributeURLToBase64Map[url]}`,
      );
    }
  }
  return attrValue;
}

export async function makeSVGPortable(svg: SVGElement) {
  // iterate over the entire object tree in the CSV and apply all computed styles as inline styles
  // to remove the dependency on outside stylesheets
  const nodeIterator = document.createNodeIterator(svg, NodeFilter.SHOW_ELEMENT);
  const baseStyles = window.getComputedStyle(svg);
  let node: Node | null = null;

  while ((node = nodeIterator.nextNode())) {
    if (!(node instanceof SVGElement || node instanceof HTMLElement)) {
      continue;
    }
    const nodeStyles = window.getComputedStyle(node);
    for (const idx of Object.keys(nodeStyles)) {
      const attrName: string = nodeStyles[idx];
      if (!USED_ATTRIBUTES.some((prefix) => attrName.startsWith(prefix))) {
        continue;
      }
      if (!node.style[attrName] && nodeStyles[attrName] !== baseStyles[attrName]) {
        node.style[attrName] = await makeAttributeValuePortable(nodeStyles[attrName]);
      }
      if (node instanceof HTMLElement) {
        node.style.boxSizing = 'border-box';
      }
    }
  }

  // Apply styles inherited from the surrounding document to the base SVG element. This
  // sets things like the line-height, font smoothing, etc.
  for (const idx of Object.keys(baseStyles)) {
    const attrName: string = baseStyles[idx];
    if (!USED_ATTRIBUTES.some((prefix) => attrName.startsWith(prefix))) {
      continue;
    }
    if (!svg.style[attrName]) {
      svg.style[attrName] = baseStyles[attrName];
    }
  }

  // Remove references to CSS classes (no longer needed)
  const removeClassesIterator = document.createNodeIterator(svg, NodeFilter.SHOW_ELEMENT);
  while ((node = removeClassesIterator.nextNode())) {
    if (node instanceof SVGElement || node instanceof HTMLElement) {
      node.removeAttribute('class');
    }
  }

  // Find all the stylesheets on the page and embed the font-face declarations into
  // the SVG document.
  const fontFaces = Array.from(document.querySelectorAll('style'))
    .flatMap((style) => (style.textContent || '').match(/@font-face ?{[^\}]*}/gim))
    .filter(Boolean);
  const styleEl = document.createElement('style');
  styleEl.textContent = fontFaces.join('\n\n');
  svg.appendChild(styleEl);
}
