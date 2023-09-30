import React from 'react';

const Sha = () => {
  return (
    <div>
      {process.env.VERCEL_GIT_COMMIT_SHA || 'SHA not available'}
    </div>
  );
};

export default Sha;
