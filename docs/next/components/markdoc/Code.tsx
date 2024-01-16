import {Transition} from '@headlessui/react';
import React, {useRef, useState} from 'react';
// import 'prismjs';
// import 'prismjs/themes/prism.css';
import Prism from 'react-prism';

import {RenderedDAG} from '../mdx/RenderedDAG';

interface CodeProps extends React.HTMLProps<HTMLElement> {
  language: string;
  dagimage?: string;
  fullwidth?: boolean;
}

// export function Code({children, language}) {
//   return (
//     <Prism key={language} component="pre" className={`language-${language}`}>
//       {children}
//     </Prism>
//   );
// }
export function Code({children, language, dagimage, fullwidth = true, ...props}: CodeProps) {
  // export const Code: React.FC<CodeProps> = ({children, language, dagimage, ...props}) => {
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  // Early exit if we're not a full width code block
  if (!fullwidth) {
    return <code {...props}>{children}</code>;
  }

  const onClick = async () => {
    try {
      await navigator.clipboard.writeText(preRef.current?.innerText);
      setCopied(true);
    } catch (err) {
      console.log('Fail to copy', err);
    }

    setTimeout(() => {
      setCopied(false);
    }, 1000);
  };

  return (
    <div className="relative" style={{display: 'flex'}}>
      <div style={{flex: '1 1 auto', position: 'relative', minWidth: 0}}>
        <Transition
          show={!copied}
          appear={true}
          enter="transition ease-out duration-150 transform"
          enterFrom="opacity-0 scale-95"
          enterTo="opacity-100 scale-100"
          leave="transition ease-in duration-150 transform"
          leaveFrom="opacity-100 scale-100"
          leaveTo="opacity-0 scale-95"
        >
          <div className="absolute top-0 right-0 mt-2 mr-2">
            <svg
              className="h-5 w-5 text-gray-400 cursor-pointer hover:text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              onClick={onClick}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
        </Transition>
        <Transition
          show={copied}
          appear={true}
          enter="transition ease-out duration-150 transform"
          enterFrom="opacity-0 scale-95"
          enterTo="opacity-500 scale-100"
          leave="transition ease-in duration-200 transform"
          leaveFrom="opacity-100 scale-100"
          leaveTo="opacity-0 scale-95"
        >
          <div className="absolute top-0 right-0 mt-1 mr-2">
            <span className="inline-flex items-center px-2 rounded text-xs font-medium leading-4 bg-gray-100 text-gray-800">
              Copied
            </span>
          </div>
        </Transition>
        <pre
          className={`language-${language}`}
          ref={preRef}
          style={{height: '100%', marginBottom: 0, marginTop: 0}}
        >
          {/* <Prism key={language} component="pre" className={`language-${language}`}>
            {children}
          </Prism> */}
          <code className={`language-${language}`} {...props}>
            {Prism.highlightElement(children)}
          </code>
        </pre>
      </div>
      {dagimage && (
        <RenderedDAG
          svgSrc={'/' + dagimage}
          mobileImgSrc="/images-2022-july/screenshots/python-assets2.png"
        />
      )}
    </div>
  );
}
