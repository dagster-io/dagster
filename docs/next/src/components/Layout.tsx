import Head from 'next/head';
import Header from './Header';
import Sidebar from './Sidebar';
import { useRouter } from 'next/router';
import { useState } from 'react';
import cx from 'classnames';

const layoutStyle = {
  margin: 20,
  padding: 20,
};

const Layout: React.FunctionComponent = (props) => {
  const router = useRouter();
  const [isNavigationVisible, setIsNavigationVisible] = useState(false);
  return (
    <>
      <Head>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      </Head>
      <div style={layoutStyle}>
        <Header
          onMobileToggleNavigationClick={() => {
            setIsNavigationVisible(!isNavigationVisible);
          }}
        />
        <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
          <div className="flex mt-16 flex-col md:flex-row">
            <div
              className={cx(
                {
                  hidden: !isNavigationVisible,
                },
                'pb-16',
                'md:pb-0',
                'md:visible',
                'md:block',
                'md:w-1/4',
              )}
            >
              <Sidebar />
            </div>
            <div
              className={cx('w-full', 'md:w-3/4', 'md:pl-16', 'md:pr-4', {
                markdown:
                  router.pathname.indexOf('docs') > 0 ||
                  router.pathname.indexOf('_modules') > 0,
              })}
            >
              {props.children}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Layout;
