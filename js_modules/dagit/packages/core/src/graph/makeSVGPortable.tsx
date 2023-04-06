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

async function convertURLToBase64Data(url: string) {
  if (!attributeURLToBase64Map[url]) {
    const data = await fetch(url);
    attributeURLToBase64Map[url] = btoa(await data.text());
  }
  return `data:image/svg+xml;base64,${attributeURLToBase64Map[url]}`;
}

async function makeAttributeValuePortable(attrValue: string) {
  // If the attribute value references a url(http:...), fetch it and convert
  // it to an inline base64 data url. (This replaces our dependency on icon SVGs)
  if (attrValue.startsWith('url(')) {
    const match = attrValue.match(/url\(['"]?(http[^'"]+)['"]?\)/);
    if (match) {
      const url = match[1];
      const data = await convertURLToBase64Data(url);
      attrValue = attrValue.replace(url, data);
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
      const attrName: string = (nodeStyles as any)[idx];
      if (!USED_ATTRIBUTES.some((prefix) => attrName.startsWith(prefix))) {
        continue;
      }
      if (
        !(node.style as any)[attrName] &&
        (nodeStyles as any)[attrName] !== (baseStyles as any)[attrName]
      ) {
        (node.style as any)[attrName] = await makeAttributeValuePortable(
          (nodeStyles as any)[attrName],
        );
      }
      if (node instanceof HTMLElement) {
        node.style.boxSizing = 'border-box';
      }
    }
    if (node instanceof HTMLImageElement) {
      const src = node.getAttribute('src');
      if (src && !src.startsWith('data:')) {
        node.setAttribute('src', await convertURLToBase64Data(src));
      }
    }
  }

  // Apply styles inherited from the surrounding document to the base SVG element. This
  // sets things like the line-height, font smoothing, etc.
  for (const idx of Object.keys(baseStyles)) {
    const attrName: string = (baseStyles as any)[idx];
    if (!USED_ATTRIBUTES.some((prefix) => attrName.startsWith(prefix))) {
      continue;
    }
    if (!(svg.style as any)[attrName]) {
      (svg.style as any)[attrName] = (baseStyles as any)[attrName];
    }
  }

  // Remove references to CSS classes (no longer needed)
  const removeClassesIterator = document.createNodeIterator(svg, NodeFilter.SHOW_ELEMENT);
  while ((node = removeClassesIterator.nextNode())) {
    if (node instanceof SVGElement || node instanceof HTMLElement) {
      node.removeAttribute('class');
    }
  }

  // Find all the stylesheets on the page and embed the font-face declarations
  // into the SVG document.
  const cssSources = Array.from<HTMLStyleElement | HTMLLinkElement>(
    document.querySelectorAll('style,link[rel=stylesheet]'),
  );
  const fontFaces = cssSources.flatMap((el) =>
    el.sheet
      ? Array.from(el.sheet.cssRules)
          .filter((r) => r instanceof CSSFontFaceRule)
          .map((r) => r.cssText)
      : [],
  );

  const styleEl = document.createElement('style');
  styleEl.textContent = fontFaces.join('\n\n');
  svg.appendChild(styleEl);
}
