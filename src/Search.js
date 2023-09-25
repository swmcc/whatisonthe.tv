import { useState } from 'react';

const Search = () => {
  const [query, setQuery] = useState('');
  const [data, setData] = useState(null);

  const fetchData = async () => {
    if (query.length >= 3) {
      const DOMAIN = process.env.REACT_APP_WHATISONTHETV_API_DOMAIN
      const response = await fetch(`${DOMAIN}/shows?query=${query}`);
      const jsonData = await response.json();
      setData(jsonData.data);
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4">

        <input
          type="text"
          className="w-full pl-10 pr-4 py-2 rounded-full border border-gray-300 focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 shadow-sm"
          placeholder="Search..."
          value={query}
          onKeyPress={fetchData}
          onChange={e => setQuery(e.target.value)}
        />

        <div className="flex justify-center space-x-4 py-4">
          <div className="flex flex-col sm:flex-row sm:space-x-2">
            <button className="bg-blue-500 text-white px-4 py-2 mb-2 sm:mb-0" onClick={fetchData}>Search</button>
            <button className="bg-blue-500 text-white px-4 py-2">I'm Feeling Curious</button>
          </div>
        </div>
      </div>

      <ul className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 sm:gap-x-6 lg:grid-cols-4 xl:gap-x-8">
        {data ? data.map((item) => (
          <li key={item.id} className="relative">

            <div className="group aspect-h-7 aspect-w-10 block w-full overflow-hidden rounded-lg bg-gray-100 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 focus-within:ring-offset-gray-100">
              <img src={item.thumbnail} alt={item.name} className="pointer-events-none object-cover group-hover:opacity-75" />
              <button type="button" className="absolute inset-0 focus:outline-none">
                <span className="sr-only">View details for {item.name}</span>
              </button>
            </div>
            <p className="pointer-events-none mt-2 block truncate text-sm font-medium text-gray-900">{item.name}</p>
            <p className="pointer-events-none block text-sm font-medium text-gray-500">{item.year}</p>
            <p className="pointer-events-none block text-sm font-medium text-gray-500">{item.type}</p>
          </li>
        )) : null}
      </ul>
    </div>
  );
};

export default Search;
