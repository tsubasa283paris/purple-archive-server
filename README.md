# Purple Archive APIサーバ

プロジェクト概要は <https://github.com/tsubasa283paris/purple-archive> を参照。

## 環境構築

環境はWSL2。

1. PostgreSQLをインストールする。  
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
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

1. Djangoを操作するためのスーパーユーザを作成する。  
   ```bash
   python manage.py createsuperuser
   ```

   ローカル環境でのデバッグに用いるだけなので、名前やパスワードは簡易なものでよい。

1. 次項「マイグレーション」を実施する。

## マイグレーション

以下は初回環境構築時の手順。  
DB定義変更時のマイグレーションの場合はデータベース作成の手順を飛ばす。

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

1. 仮想環境を起動する。  
   ```bash
   source .venv/bin/activate
   ```

1. 以下のコマンドを実行し、マイグレーションを実施する。  
   ```bash
   python manage.py makemigrations
   python manage.py migrate
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
   python manage.py runserver
   ```
