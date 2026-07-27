import path from 'node:path';

const config = {
  transpilePackages: ['@bet-score/contracts'],
  turbopack: {
    root: path.join(import.meta.dirname, '..'),
  },
};

export default config;
