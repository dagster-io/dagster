import NextImage from 'next/image';
import {useEffect, useState} from 'react';
import Zoom from 'react-medium-image-zoom';

export const MyImage = ({children, ...props}) => {
  // Manually set dimensions for images will be on props.width and props.height.
  // Images without manual ddimensions will use the dimensions state and
  // automatically set width and height as an effect in the client.

  const [dimensions, setDimensions] = useState({width: 0, height: 0});
  /* Only version images when all conditions meet:
   * - use <Image> component in mdx
   * - on non-master version
   * - in public/images/ dir
   */
  const {src} = props;

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setDimensions({width: img.width, height: img.height});
    };
  }, [src]);

  if (!src.startsWith('/images/')) {
    return (
      <span className="block mx-auto">
        <NextImage {...(props as any)} />
      </span>
    );
  }
  return (
    <Zoom wrapElement="span" wrapStyle={{display: 'block'}}>
      <span className="block mx-auto">
        <NextImage
          src={src}
          width={props.width || dimensions.width}
          height={props.height || dimensions.height}
          alt={props.alt}
        />
      </span>
    </Zoom>
  );
};
