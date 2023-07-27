# Purple Archive APIサーバ

プロジェクト概要は <https://github.com/tsubasa283paris/purple-archive> を参照。

## 環境構築

環境はWSL2。

1. Poetryをインストールする。  
   <https://python-poetry.org/docs/>

1. （任意）  
   VSCodeでインタープリターによるライブラリ情報の取得を行うため、仮想環境をプロジェクト内に配置する設定を行う。  
   なお、仮想環境情報を格納した `.venv` はデフォルトでGitに追跡されないよう.gitignoreが追加される。  
   ```bash
   poetry config virtualenvs.in-project true
   ```

1. 当リポジトリにおいて `poetry install` を実施する。  

1. 仮想環境を起動する。  
   ```bash
   source .venv/bin/activate
   ```

1. サーバを起動する。  
   ```bash
   python manage.py runserver
   ```
