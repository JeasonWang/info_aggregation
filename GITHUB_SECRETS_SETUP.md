# Info_aggregation GitHub Secrets 配置

在后端仓库 `Settings -> Secrets and variables -> Actions` 中配置以下内容。

## DockerHub

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## 服务器

- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_SSH_KEY`
- `SERVER_DEPLOY_PATH`
  - 例如：`/opt/info-aggregation`

## 数据库

如果用 SQLite：

- `DB_TYPE=sqlite`
- `DB_HOST=` 留空
- `DB_PORT=3306`
- `DB_USER=` 留空
- `DB_PASSWORD=` 留空
- `DB_NAME=info_aggregation`
- `LOG_LEVEL=INFO`

如果用 MySQL：

- `DB_TYPE=mysql`
- `DB_HOST=你的数据库地址`
- `DB_PORT=3306`
- `DB_USER=用户名`
- `DB_PASSWORD=密码`
- `DB_NAME=info_aggregation`
- `LOG_LEVEL=INFO`
