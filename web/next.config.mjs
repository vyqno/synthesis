import path from "path";
import { fileURLToPath } from "url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const config = {
  webpack: (config) => {
    config.resolve = {
      ...config.resolve,
      alias: {
        ...(config.resolve.alias || {}),
        "@safe-global/safe-apps-sdk": path.resolve(__dirname, "stubs/safe-apps-sdk.js"),
      },
      fallback: {
        ...(config.resolve.fallback || {}),
        "socket.io-client": false,
        bufferutil: false,
        "utf-8-validate": false,
      },
    };
    return config;
  },
};
export default config;
