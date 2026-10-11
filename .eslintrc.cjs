module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: ['eslint:recommended', 'plugin:react-hooks/recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } },
  plugins: ['react'],
  rules: { 'react/jsx-uses-vars': 'error', 'react/jsx-uses-react': 'off' },
  ignorePatterns: ['dist', 'node_modules', '.venv', '*.canvas.tsx'],
  overrides: [
    { files: ['*.cjs'], env: { node: true } },
    { files: ['tests/*.js'], env: { node: true, browser: false } },
  ],
};
