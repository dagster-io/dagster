import * as React from 'react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';

const Layout: React.FC = ({children}) => {
  const [isMobileDocsMenuOpen, setMobileDocsMenuOpen] = React.useState<boolean>(false);
  const openMobileDocsMenu = () => {
    setMobileDocsMenuOpen(true);
  };
  const closeMobileDocsMenu = () => {
    setMobileDocsMenuOpen(false);
  };

  return (
    <>
      <div
        style={{
          minHeight: '100vh',
          backgroundImage: 'url("/assets/head-texture.jpg")',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'top middle',
          backgroundSize: 'fit',
          backgroundColor: '#FAF9F7',
        }}
      >
        <Header openMobileDocsMenu={openMobileDocsMenu} />
        <div className="w-screen mx-auto px-4 sm:px-6 lg:px-8" style={{paddingTop: '64px'}}>
          <div className="mt-10 flex justify-center">
            <Sidebar
              isMobileDocsMenuOpen={isMobileDocsMenuOpen}
              closeMobileDocsMenu={closeMobileDocsMenu}
            />
            <div className="lg:pl-80 flex w-full">{children}</div>
          </div>
        </div>
      </div>
    </>
  );
};

export const getLayout = (page: React.ReactNode) => <Layout>{page}</Layout>;

export default Layout;
