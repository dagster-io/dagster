/** @jsx jsx */
import { jsx, SxStyleProp } from "theme-ui";
import styleToObj from "style-to-object";
import ModalImage from "react-modal-image";

export const imgStyle: SxStyleProp & {
  "-webkit-box-shadow": string;
  "-moz-box-shadow": string;
} = {
  border: "1px solid #333",
  boxShadow: "5px 5px 5px 0px rgba(0, 0, 0, 0.75)",
  "-webkit-box-shadow": "5px 5px 5px 0px rgba(0, 0, 0, 0.75)",
  "-moz-box-shadow": "5px 5px 5px 0px rgba(0, 0, 0, 0.75)"
};

type ImageProps = JSX.IntrinsicElements["img"] & {
  src?: string;
  width?: string;
  images: any[];
  style?: string | object;
};

export const Image: React.FC<ImageProps> = ({
  src,
  width = "100%",
  images,
  style,
  ...props
}) => {
  const img = images.find(({ node }) => node.absolutePath.includes(src));
  const st = {
    ...imgStyle,
    ...(typeof style === "string" ? styleToObj(style) : style)
  };

  if (img) {
    return (
      <ModalImage
        hideZoom
        imageBackgroundColor="transparent"
        small={img.node.childImageSharp.fluid.src}
        smallSrcSet={img.node.childImageSharp.fluid.srcSet}
        large={img.node.childImageSharp.original.src}
        sx={{ width, ...st }}
      />
    );
  } else {
    // TODO: Let's correct this with some testing.
    // There's several issues with this code:
    // 1- style is being modified and it comes from a parameter
    // this could lead to the heap being modified resulting in
    // unexpected behavior.
    // 2- props.style will be overwritten by the style tag, so,
    // why does this line still exists?
    // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
    // @ts-ignore
    props.style = { ...imgStyle, ...props.style };
    // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
    // @ts-ignore
    return <img src={src} {...props} alt={props.alt} style={st} />;
  }
};
