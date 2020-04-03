import Head from 'next/head';
import Header from './Header';
import Sidebar from './Sidebar';
import { useRouter } from 'next/router';

const layoutStyle = {
  margin: 20,
  padding: 20,
};

const Layout: React.FunctionComponent = (props) => {
  const router = useRouter();
  return (
    <>
      <Head>
        <link rel="stylesheet" href="https://rsms.me/inter/inter.css" />
      </Head>
      <div style={layoutStyle}>
        <Header />
        <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
          <div className="flex mt-16">
            <div className="w-1/4">
              <Sidebar />
            </div>
            <div
              className={`w-3/4 pl-16 pr-4 ${
                router.pathname.indexOf('docs') > 0 ||
                router.pathname.indexOf('_modules') > 0
                  ? 'markdown'
                  : ''
              }`}
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
