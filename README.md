# Purple Archive APIサーバ

プロジェクト概要は <https://github.com/tsubasa283paris/purple-archive> を参照。

## 環境構築

環境はWSL2。

1. PostgreSQLをインストールする。  
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

1. Pythonパッケージのインストールに必要ないくつかのパッケージをインストールする。  
   ```bash
   sudo apt install python3-dev libpq-dev
   ```

1. Poetryをインストールする。  
   <https://python-poetry.org/docs/>

1. （任意）  
   VSCodeでインタープリターによるライブラリ情報の取得を行うため、仮想環境をプロジェクト内に配置する設定を行う。  
   なお、仮想環境情報を格納した `.venv` はデフォルトでGitに追跡されないよう.gitignoreが追加される。  
   ```bash
   poetry config virtualenvs.in-project true
   ```

1. 当リポジトリにおいて `poetry install` を実施する。  

1. PostgreSQLサーバを起動する。  
   ```bash
   sudo service postgresql start
   ```

1. データベース `purple_archive_db` を作成する。  
   ```bash
   sudo -u postgres psql
   ```

   ```sql
   CREATE DATABASE purple_archive_db;
   ```

1. 次項「マイグレーション（同期）」を実施する。

以下、「仮想環境内で実施する」と表現した場合は下記のコマンドによってpoetryの作成した仮想環境を起動して実施することを指す。  
（同仮想環境内で `deactivate` とだけ実行すると仮想環境を終了する。）  
```bash
source .venv/bin/activate
```

## マイグレーション（同期）

当リポジトリの `alembic/versions` ディレクトリに保存されているマイグレーションバージョン（以下リビジョン）をすべて適用する。  

仮想環境内で実施する。  
```bash
alembic upgrade head
```

なお、`alembic downgrade` など特定のリビジョンに巻き戻すことも可能である。  
詳細は <https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration> を参照。

## マイグレーション（作成）

当リポジトリの `sql_interface/models.py` に行った変更をリビジョンとして保存する。  
即座にローカルデータベースに反映する場合は「マイグレーション（同期）」を実施する。  

仮想環境内で実施する。  
```bash
alembic revision --autogenerate -m "<リビジョンメッセージ>"
```

## 起動（デバッグ）

1. PostgreSQLサーバを起動する。  
   ```bash
   sudo service postgresql start
   ```

1. 仮想環境を起動する。  
   ```bash
   source .venv/bin/activate
   ```

1. サーバを起動する。  
   ```bash
   uvicorn main:app --reload
   ```
