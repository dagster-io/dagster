import NextImage from 'next/image';
import Zoom from 'react-medium-image-zoom';

export const Image = ({children, ...props}) => {
  /* Only version images when all conditions meet:
   * - use <Image> component in mdx
   * - on non-master version
   * - in public/images/ dir
   */
  const {src} = props;
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
        <NextImage src={src} width={props.width} height={props.height} alt={props.alt} />
      </span>
    </Zoom>
  );
};
