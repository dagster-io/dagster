// import * as React from 'react';

// import Header from '../components/Header';
// import Sidebar from '../components/Sidebar';
// import {VersionedContentLayout} from '../components/mdx/MDXRenderer';

// const Layout: React.FC = ({children}) => {
//   const [isMobileDocsMenuOpen, setMobileDocsMenuOpen] = React.useState<boolean>(false);
//   const openMobileDocsMenu = () => {
//     setMobileDocsMenuOpen(true);
//   };
//   const closeMobileDocsMenu = () => {
//     setMobileDocsMenuOpen(false);
//   };

//   return (
//     <>
//       <div
//         style={{
//           minHeight: '100vh',
//           backgroundImage: 'url("/_next/image?url=/assets/head-texture.jpg&w=3840&q=100")',
//           backgroundRepeat: 'no-repeat',
//           backgroundPosition: 'top middle',
//           backgroundSize: 'fit',
//           backgroundColor: '#FAF9F7',
//         }}
//       >
//         <Header openMobileDocsMenu={openMobileDocsMenu} />
//         <div className="w-screen mx-auto px-4 sm:px-6 lg:px-8" style={{paddingTop: '48px'}}>
//           <div className="mt-8 flex justify-center">
//             <Sidebar
//               isMobileDocsMenuOpen={isMobileDocsMenuOpen}
//               closeMobileDocsMenu={closeMobileDocsMenu}
//             />
//             {/* <div className="lg:pl-80 flex w-full prose">{children}</div> */}
//             <div className="lg:pl-80 flex w-full prose">
//               <VersionedContentLayout asPath={asPath}>
//                 <div className="DocSearch-content prose dark:prose-dark max-w-none">{content}</div>
//               </VersionedContentLayout>

//               <RightSidebar
//                 editMode={editMode}
//                 navigationItems={navigationItems}
//                 githubLink={githubLink}
//                 toggleFeedback={toggleFeedback}
//               />
//             </div>
//           </div>
//         </div>
//       </div>
//     </>
//   );
// };

// export const getLayout = (page: React.ReactNode) => <Layout>{page}</Layout>;

// export default Layout;
