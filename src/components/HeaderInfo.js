import React from 'react';

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

export default HeaderInfo;
