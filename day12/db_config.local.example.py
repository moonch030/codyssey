# 이 파일을 db_config.local.py 로 복사한 뒤 본인 MySQL 비밀번호를 넣으세요.
# db_config.local.py 는 .gitignore 에 등록되어 git 에 올라가지 않습니다.

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',          # Workbench 접속 계정 (예: root, dvely)
    'password': '여기에_비밀번호',
    'database': 'codyssey',
}

# 또는 아래 한 줄만 써도 됩니다.
# MYSQL_PASSWORD = '여기에_비밀번호'
