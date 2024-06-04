import sizeOf from 'image-size';
import fs from 'fs';
import path from 'path';

const getImageDimensions = async (url: string) => {
  const response = await fetch(url);
  const arrayBuffer = await response.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);
  const dimensions = sizeOf(buffer);
  return dimensions;
};

export default getImageDimensions;
