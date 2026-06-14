import React from 'react';

const BackgroundMesh = ({ fixed = false }) => {
  return (
    <div className={`bg-mesh ${fixed ? 'fixed-bg' : ''}`}></div>
  );
};

export default BackgroundMesh;
