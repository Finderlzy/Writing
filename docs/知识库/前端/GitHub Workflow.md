## 解决什么问题
前端代码写完后，由于都会经过[[构建（Build）|Build]]和[[部署（Deploy）与托管（Hosting）|Deploy]]这两步。如果每次都手动build和deploy，既繁琐，又容易出现遗漏（因为build有很多步骤）。
## 是什么
Github Workflow就是一个机器人，可以帮我们自动完成build和deploy。
## 怎么用
写一个 **`deploy.yml`** 文档就可以了。
```yaml
// deploy.yml

name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Check
        run: pnpm check

      - name: Build
        run: pnpm build

      - name: Configure Pages
        uses: actions/configure-pages@v5

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: dist
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```
