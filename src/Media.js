import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';

function HeaderInfo({ data }) {

  let synopsis = '';
  if (data && data.translations.overviewTranslations) {
    const filteredOverview = data.translations.overviewTranslations
      .filter(item => item.language === 'eng')
      .map(item => item.overview);

    synopsis = filteredOverview[0];
  }

  return (
    <div className="flex flex-col items-start">

      <div className="text-4xl mb-4 font-bold">
        {data ? data.name : 'Loading...'}
      </div>

      <div className="flex flex-grow items-start">
        {/* Image container */}
        <div className="flex-initial">
          {data && data.image ? (
            <img src={data.image} alt={data.name} className="object-contain h-96" />
          ) : null}
        </div>

        <div className="px-4"></div>

        {/* Synopsis container */}
        <div className="flex-1 text-left">
          <p className="mt-1 max-w-2xl text-sm leading-6 text-gray-500">
            {synopsis}
          </p>
        </div>
      </div>
    </div>

  );
}

function General({ fetchedData }) {
  return (
    <div>
      <div className="mt-6 border-t border-gray-100">
        <dl className="divide-y divide-gray-100">
          <div className="px-4 py-6 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium leading-6 text-gray-900">Status</dt>
            <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">Margot Foster</dd>
          </div>
          <div className="px-4 py-6 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium leading-6 text-gray-900">Genres</dt>
            <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">Backend Developer</dd>
          </div>
          <div className="px-4 py-6 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium leading-6 text-gray-900">Aired</dt>
            <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">margotfoster@example.com</dd>
          </div>
          <div className="px-4 py-6 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
            <dt className="text-sm font-medium leading-6 text-gray-900">Network</dt>
            <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0">$120,000</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

function CastCrew({ fetchedData }) {
  return (
    <div>
      Cast & Crew
    </div>
  );
}

function Seasons({ fetchedData }) {
  return (
    <div>
      Seasons
    </div>
  );
}

function Lists({ fetchedData }) {
  return (
    <div>
      Lists
    </div>
  );
}


function Media() {
  const { id: paramId } = useParams();
  const parts = paramId.split('-');
  const [type, id] = parts;

  const [data, setData] = useState(null);

  const fetchData = async () => {
    const DOMAIN = process.env.REACT_APP_WHATISONTHETV_API_DOMAIN;
    const validTypes = ['movie', 'person', 'series'];

    if (!validTypes.includes(type)) {
      console.error('Invalid type');
      return;
    }

    const endpoint = `${DOMAIN}/${type}/${id}`;
    const response = await fetch(endpoint);
    const jsonData = await response.json();
    setData(jsonData.data);
  };

  useEffect(() => {
    fetchData();
  }, [id]);

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
