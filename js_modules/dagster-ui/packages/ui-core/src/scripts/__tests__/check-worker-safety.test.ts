import {jest} from '@jest/globals';
import * as ts from 'typescript';

import {findUnsafeApiUsages, generateErrorMessage} from '../worker-safety/ast-analyzer';
import {WorkerSafetyChecker} from '../worker-safety/checker';
import {UNSAFE_BROWSER_APIS, UNSAFE_IMPORTS} from '../worker-safety/types';

// Mock dependencies
jest.mock('glob');
jest.mock('fs');

describe('WorkerSafetyChecker - Types and Constants', () => {
  it('should include all expected unsafe browser APIs', () => {
    expect(UNSAFE_BROWSER_APIS.has('window')).toBe(true);
    expect(UNSAFE_BROWSER_APIS.has('document')).toBe(true);
    expect(UNSAFE_BROWSER_APIS.has('navigator')).toBe(true);
    expect(UNSAFE_BROWSER_APIS.has('localStorage')).toBe(true);
    expect(UNSAFE_BROWSER_APIS.has('location')).toBe(true);
    expect(UNSAFE_BROWSER_APIS.has('requestAnimationFrame')).toBe(true);
  });

  it('should include all expected unsafe imports', () => {
    expect(UNSAFE_IMPORTS.has('react')).toBe(true);
    expect(UNSAFE_IMPORTS.has('react-dom')).toBe(true);
    expect(UNSAFE_IMPORTS.has('@apollo/client')).toBe(true);
    expect(UNSAFE_IMPORTS.has('react-router')).toBe(true);
  });
});

describe('AST Analyzer', () => {
  function createSourceFile(code: string): ts.SourceFile {
    return ts.createSourceFile('test.ts', code, ts.ScriptTarget.Latest, true);
  }

  describe('findUnsafeApiUsages', () => {
    it('should find unsafe browser API usage', () => {
      const code = `window.localStorage.setItem('key', 'value');`;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(1);
      expect(usages[0]?.api).toBe('window');
      expect(usages[0]?.type).toBe('api');
    });

    it('should find unsafe imports', () => {
      const code = `import React from 'react';`;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(1);
      expect(usages[0]?.api).toBe('import react');
      expect(usages[0]?.type).toBe('import');
    });

    it('should not flag guarded usage', () => {
      const code = `
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('key', 'value');
        }
      `;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(0);
    });

    it('should not flag property names', () => {
      const code = `obj.location.href = 'test';`;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(0);
    });

    it('should not flag shadowed variables', () => {
      const code = `
        function test(window: any) {
          return window.someProperty;
        }
      `;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(0);
    });

    it('should handle ternary expressions correctly', () => {
      const code = `
        const lang = typeof navigator !== 'undefined' ? navigator.language : 'en-US';
      `;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(0);
    });

    it('should not flag qualified type names', () => {
      const code = `const nodes: {[key: string]: dagre.Node} = {};`;
      const sourceFile = createSourceFile(code);
      const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

      expect(usages).toHaveLength(0);
    });
  });

  describe('generateErrorMessage', () => {
    it('should generate appropriate messages for API usage', () => {
      expect(generateErrorMessage('window', 'api')).toContain('not available in worker context');
      expect(generateErrorMessage('requestAnimationFrame', 'api')).toContain(
        'setTimeout/setInterval instead',
      );
      expect(generateErrorMessage('navigator', 'api')).toContain('userAgent from worker context');
      expect(generateErrorMessage('localStorage', 'api')).toContain('IndexedDB');
    });

    it('should generate appropriate messages for imports', () => {
      expect(generateErrorMessage('import react', 'import')).toContain('increases bundle size');
      expect(generateErrorMessage('import @apollo/client', 'import')).toContain('GraphQL client');
    });
  });
});

describe('WorkerSafetyChecker Integration', () => {
  // Note: WorkerSafetyChecker requires a TypeScript project with tsconfig.json
  // These tests verify the public interface exists

  it('should have the expected class interface', () => {
    expect(typeof WorkerSafetyChecker).toBe('function');
  });

  it('should export the expected constructor', () => {
    expect(WorkerSafetyChecker.prototype.constructor).toBe(WorkerSafetyChecker);
  });
});

describe('Complex Edge Cases Integration', () => {
  function createSourceFile(code: string): ts.SourceFile {
    return ts.createSourceFile('test.ts', code, ts.ScriptTarget.Latest, true);
  }

  it('should handle the navigator.language ternary case correctly', () => {
    const code = `
      const formatMsecMantissa = (msec: number) =>
        msecFormatter(typeof navigator !== 'undefined' ? navigator.language : 'en-US')
          .format(msec / 1000)
          .slice(-4);
    `;
    const sourceFile = createSourceFile(code);
    const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

    // Should not flag navigator because it's properly guarded
    expect(usages).toHaveLength(0);
  });

  it('should handle the dagre.Node type case correctly', () => {
    const code = `
      const ops: {[opName: string]: OpLayout} = {};
      const dagreNodes: {[opName: string]: dagre.Node} = {};
    `;
    const sourceFile = createSourceFile(code);
    const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

    // Should not flag Node because it's a qualified type name
    expect(usages).toHaveLength(0);
  });

  it('should handle multiple patterns in one file', () => {
    const code = `
      import React from 'react';
      
      if (typeof window !== 'undefined') {
        window.localStorage.setItem('key', 'value'); // Should not flag - guarded
      }
      
      const lang = typeof navigator !== 'undefined' ? navigator.language : 'en-US'; // Should not flag - guarded
      
      function test(document: any) {
        return document.title; // Should not flag - shadowed
      }
      
      alert('unsafe!'); // Should flag - unguarded
    `;
    const sourceFile = createSourceFile(code);
    const usages = findUnsafeApiUsages(sourceFile, 'test.ts');

    // Should only flag React import and alert
    expect(usages).toHaveLength(2);
    expect(usages.some((u) => u.api === 'import react')).toBe(true);
    expect(usages.some((u) => u.api === 'alert')).toBe(true);
  });
});
