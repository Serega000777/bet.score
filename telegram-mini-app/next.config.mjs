import path from 'node:path';

const config = {
  turbopack: {
    root: path.join(import.meta.dirname, '..'),
  },
};

export default config;
