import 'prismjs';
import 'prismjs/themes/prism.css';

import Prism from 'react-prism';

export function Code({children, language}) {
  return (
    <Prism key={language} component="pre" className={`language-${language}`}>
      {children}
    </Prism>
  );
}
