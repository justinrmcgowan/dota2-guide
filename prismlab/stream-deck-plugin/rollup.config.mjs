import { nodeResolve } from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import typescript from "@rollup/plugin-typescript";

export default {
  input: "src/plugin.ts",
  output: {
    file: "com.prismlab.dota2.sdPlugin/bin/plugin.js",
    format: "cjs",
    sourcemap: true,
  },
  plugins: [
    nodeResolve({ preferBuiltins: true }),
    commonjs(),
    typescript({ tsconfig: "./tsconfig.json" }),
  ],
  external: [],
};
