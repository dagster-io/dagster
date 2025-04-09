import {defineConfig} from 'eslint/config';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier/flat';

export default defineConfig([tseslint.configs.recommended, eslintConfigPrettier]);
