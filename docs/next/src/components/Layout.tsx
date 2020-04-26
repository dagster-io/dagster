import Head from 'next/head';
import Header from './Header';
import SidebarDesktop from './Sidebar/SidebarDesktop';
import SidebarMobile from './Sidebar/SidebarMobile';
import { useState } from 'react';
import cx from 'classnames';
import { useRouter } from 'next/router';
import OnThisPage from './OnThisPage';
import { useAnchorHeadings } from 'hooks/AnchorHeadings';
import { PrevNext } from './PrevNext';

const Layout: React.FunctionComponent = (props) => {
  const [isNavigationVisible, setIsNavigationVisible] = useState(false);
  const router = useRouter();
  const { anchors } = useAnchorHeadings();
  const anchorHeadings = Object.values(anchors);
  return (
    <>
      <Head>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      </Head>

      <Header
        onMobileToggleNavigationClick={() => {
          setIsNavigationVisible(!isNavigationVisible);
        }}
      />

      <div className="h-screen flex overflow-hidden bg-white pt-16">
        <SidebarMobile
          isNavigationVisible={isNavigationVisible}
          setIsNavigationVisible={setIsNavigationVisible}
        />
        <SidebarDesktop />
        <div className="flex flex-col w-0 flex-1">
          <main
            className="flex-1 relative z-0 overflow-y-auto pt-2 pb-6 focus:outline-none md:py-6"
            tabIndex={0}
          >
            <div className={cx('max-w-7xl mx-auto px-4 sm:px-6 md:px-8')}>
              <div className="flex justify-between">
                <div
                  className={cx('flex-1 overflow-hidden', {
                    markdown:
                      router.pathname.indexOf('docs') > 0 ||
                      router.pathname.indexOf('_modules') > 0,
                  })}
                >
                  <>
                    {props.children}
                    <PrevNext />
                  </>
                </div>
                <OnThisPage anchors={anchorHeadings} />
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default Layout;
