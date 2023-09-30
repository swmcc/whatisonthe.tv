import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';

import HeaderInfo from './components/HeaderInfo';
import General from './components/General';
import CastCrew from './components/CastCrew';
import Seasons from './components/Seasons';
import Lists from './components/Lists';
import MediaImport from './components/MediaImport';

function Media() {
  const { id: paramId } = useParams();
  const parts = paramId.split('-');
  const [type, id] = parts;

  const data = MediaImport(type, id);

  const tabs = [
    { name: 'General', href: '#', current: true },
    { name: 'Cast & Crew', href: '#', current: false },
    ...(type === 'series' ? [{ name: 'Seasons', href: '#', current: false }] : []),
    { name: 'Lists', href: '#', current: false },

  ]

  const [currentTab, setCurrentTab] = useState('General');

  function classNames(...classes) {
    return classes.filter(Boolean).join(' ')
  }

  return (
    <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
      <HeaderInfo data={data} />
      <div className="mt-4">
        <div className="sm:hidden">
          <label htmlFor="current-tab" className="sr-only">
            Select a tab
          </label>
          <select
            id="current-tab"
            name="current-tab"
            className="block w-full rounded-md border-0 py-1.5 pl-3 pr-10 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600"
            defaultValue={tabs.find((tab) => tab.current).name}
          >
            {tabs.map((tab) => (
              <option key={tab.name}>{tab.name}</option>
            ))}
          </select>
        </div>
        <div className="hidden sm:block">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <a
                key={tab.name}
                href={tab.href}
                className={classNames(
                  currentTab === tab.name
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
                  'whitespace-nowrap border-b-2 px-1 pb-4 text-sm font-medium'
                )}
                aria-current={tab.current ? 'page' : undefined}
                onClick={() => setCurrentTab(tab.name)}
              >
                {tab.name}
              </a>
            ))}
          </nav>
        </div>


        <div className="mt-4 text-left">
          {currentTab === 'General' && <General fetchedData={data} />}
          {currentTab === 'Cast & Crew' && <CastCrew fetchedData={data} />}
          {currentTab === 'Seasons' && <Seasons fetchedData={data} />}
          {currentTab === 'Lists' && <Lists fetchedData={data} />}
        </div>
      </div>
    </div>
  )
}

export default Media;
