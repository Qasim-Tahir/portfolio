import js from '@eslint/js';
import globals from 'globals';
import hooks from 'eslint-plugin-react-hooks';

export default [
  { ignores: ['dist/**', 'node_modules/**', '.venv/**', '**/*.canvas.tsx'] },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest', sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: globals.browser,
    },
    plugins: { 'react-hooks': hooks },
    rules: {
      ...js.configs.recommended.rules,
      ...hooks.configs.recommended.rules,
    },
  },
  { files: ['tests/**/*.js', '*.config.js'], languageOptions: { globals: globals.node } },
];
