module.exports = {
  env: { node: true, es2022: true },
  extends: ["eslint:recommended", "plugin:n/recommended", "plugin:promise/recommended"],
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  rules: {
    "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
    "n/no-missing-import": "off"
  }
};
