/** @jsx jsx */
import { Styled, jsx } from 'theme-ui'
import { useRef, useEffect } from 'react'
import hljs from 'highlight.js'
import python from 'highlight.js/lib/languages/python'
import yaml from 'highlight.js/lib/languages/yaml'
import bash from 'highlight.js/lib/languages/bash'

import * as styles from './styles'

hljs.registerLanguage('python', python)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('bash', bash)

export const Pre = ({ children, ...props }) => {
  const ref = useRef()
  const language = props['data-language'] || 'bash'

  useEffect(() => {
    hljs.highlightBlock(ref.current)
  }, [])

  return (
    <Styled.pre sx={styles.wrapper} {...props}>
      <Styled.code ref={ref} className={`language-${language}`}>
        {children}
      </Styled.code>
    </Styled.pre>
  )
}
