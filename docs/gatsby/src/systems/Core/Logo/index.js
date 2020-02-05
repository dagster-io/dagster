/** @jsx jsx */
import { jsx } from 'theme-ui'
import { useStaticQuery, graphql } from 'gatsby'
import Img from 'gatsby-image'

export const Logo = props => {
  const data = useStaticQuery(
    graphql`
      query LogoImage {
        placeholderImage: file(relativePath: { eq: "logo.png" }) {
          childImageSharp {
            fluid(maxWidth: 150) {
              ...GatsbyImageSharpFluid
            }
          }
        }
      }
    `,
  )

  return <Img {...props} fluid={data.placeholderImage.childImageSharp.fluid} />
}
