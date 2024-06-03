import NextImage from 'next/image';
import Zoom from 'react-medium-image-zoom';

const getImageDimensions = (src) => {
  console.log("getImageDimensions src works?", src);
  return new Promise((resolve, reject) => {
    const img = new Image();
    console.log('inside getImageDimensions Img', img);
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = (err) => {
      reject(err);
    };
    img.src = src;
  });
};

export const MyImage = ({children, ...props}) => {
  console.log('Image', props);
  /* Only version images when all conditions meet:
   * - use <Image> component in mdx
   * - on non-master version
   * - in public/images/ dir
   */
  const {src} = props;
  console.log('src', src);
  // Handle External Images
  if (!src.startsWith('/images/')) {
    return (
      <span className="block mx-auto">
        <NextImage {...(props as any)} />
      </span>
    );
  }
  // Handle Internal Images
  return (
    <span className="block mx-auto">
      <NextImage src={src} width={props.width} height={props.height} alt={props.alt} />
    </span>
  );
};
