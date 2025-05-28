export default {
  testEnvironment: 'jsdom',
  transform: { '^.+\\.jsx?$': 'babel-jest' },
  transformIgnorePatterns: ['/node_modules/'],
  moduleNameMapper: { '\\.(css|less)$': 'identity-obj-proxy' },
  setupFilesAfterEnv: ['@testing-library/jest-dom', './jest.setup.js']
};
