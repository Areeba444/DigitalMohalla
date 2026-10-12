// https://docs.expo.dev/guides/using-eslint/ (flat config, Expo SDK 57)
const { defineConfig, globalIgnores } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  // build output and the generated API types are not hand-written code
  globalIgnores(['dist/*', 'web-build/*', '.expo/*', 'src/api/schema.d.ts']),
]);
