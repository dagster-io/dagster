import Nav from './Nav';

const SidebarDesktop: React.FC = () => {
  return (
    <div className="hidden md:flex md:flex-shrink-0">
      <div className="flex flex-col w-64 border-r border-gray-200 bg-white">
        <div className="h-0 flex-1 flex flex-col pb-4 overflow-y-auto">
          <Nav className="flex-1 pt-2 px-2" />
        </div>
      </div>
    </div>
  );
};

export default SidebarDesktop;
