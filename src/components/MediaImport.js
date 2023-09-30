import { useState, useEffect } from 'react';

function MediaImport(type, id) {
  const [data, setData] = useState(null);

  const fetchData = async () => {
    const DOMAIN = process.env.REACT_APP_WHATISONTHETV_API_DOMAIN;
    const validTypes = ['movie', 'person', 'series'];

    if (!validTypes.includes(type)) {
      console.error('Invalid type');
      return;
    }

    const endpoint = `${DOMAIN}/${type}/${id}`;
    try {
      const response = await fetch(endpoint);
      if (response.ok) {
        const jsonData = await response.json();
        setData(jsonData.data);
      } else {
        console.error('Failed to fetch data:', response.statusText);
      }
    } catch (error) {
      console.error('An error occurred:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [type, id]); // dependencies ensure that fetchData will be re-called if type or id changes

  return data;
}

export default MediaImport;
