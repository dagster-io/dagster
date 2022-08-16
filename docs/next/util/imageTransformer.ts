import path from 'path';

import {Node} from 'hast';
import sizeOf from 'image-size';
import {parse} from 'node-html-parser';
import visit from 'unist-util-visit';

const PUBLIC_DIR = path.join(__dirname, '../public/');

interface ImageNode extends Node {
  type: string;
  url: string;
  alt: string;
  value: string;
}

export interface ImageStats {
  totalImages: number;
  updatedImages: string[];
}

interface ImageTransformerOptions {
  setImageStats?: (newStats: ImageStats) => void;
}

const getHTMLImageElement = (node: ImageNode) => {
  // handle <img>
  if (node.type === 'html') {
    const root = parse(node.value);
    const imgElements = root.querySelectorAll('img');
    if (imgElements.length > 0) {
      return imgElements[0];
    }
  }
  return;
};

export default ({setImageStats}: ImageTransformerOptions) =>
  async (tree: Node) => {
    const stats: ImageStats = {
      totalImages: 0,
      updatedImages: [],
    };
    const images: ImageNode[] = [];

    visit(tree, ['image', 'html'], (node: ImageNode) => {
      if (node.type === 'html') {
        if (getHTMLImageElement(node)) {
          images.push(node);
        }
      } else {
        images.push(node);
      }
    });

    for (const node of images) {
      const imgElement = getHTMLImageElement(node);
      const imageUrl = imgElement ? imgElement.attrs.src : node.url;
      const imageAlt = imgElement ? imgElement.attrs.alt : node.alt;

      // Skip external images
      if (imageUrl.startsWith('/')) {
        stats.totalImages++;
        const fileAbsPath = path.join(PUBLIC_DIR, imageUrl);
        const dimensions = sizeOf(fileAbsPath);
        const imageValue = `<Image ${
          imageAlt ? `alt="${imageAlt}" ` : ''
        }src="${imageUrl}" width={${dimensions.width}} height={${dimensions.height}} />`;

        // Convert original node to Image
        if (node.value !== imageValue) {
          node.type = 'html';
          node.value = imageValue;
          stats.updatedImages.push(node.value as string);
        }
      }
    }

    if (setImageStats) {
      setImageStats(stats);
    }
  };
