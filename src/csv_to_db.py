import os
import glob
import pandas as pd
from sqlalchemy import create_engine
import pymysql
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# pymysql을 sqlalchemy가 인식할 수 있도록 설정
pymysql.install_as_MySQLdb()


def find_latest_csv_file(directory):
    """지정된 디렉토리에서 가장 최근에 수정된 csv 파일을 찾습니다."""
    list_of_files = glob.glob(os.path.join(directory, '*.csv'))
    if not list_of_files:
        print(f"!! 오류: '{directory}' 폴더에 CSV 파일이 없습니다.")
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"▶ 가장 최근 CSV 파일을 찾았습니다: {os.path.basename(latest_file)}")
    return latest_file


def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """다운로드한 CSV의 데이터프레임을 DB 스키마에 맞게 변환합니다."""
    print("\n▶ 데이터프레임 변환을 시작합니다...")
    column_map = {
        '지점': 'station_id',
        '지점명': 'station_name',
        '일시': 'observed_date'
    }
    df = df.rename(columns=column_map)
    print("  - 컬럼명을 영문으로 변경했습니다.")

    df['station_id'] = pd.to_numeric(df['station_id'])
    df['observed_date'] = pd.to_datetime(df['observed_date'])
    spi_columns = [col for col in df.columns if 'SPI' in col]
    for col in spi_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    print("  - 데이터 타입을 DB에 맞게 변환했습니다.")

    final_columns = [
        'station_id', 'station_name', 'observed_date',
        'SPI1', 'SPI2', 'SPI3', 'SPI4', 'SPI5', 'SPI6',
        'SPI9', 'SPI12', 'SPI18', 'SPI24'
    ]
    df = df[final_columns]
    print("▶ 데이터프레임 변환 완료.")
    return df


def insert_data_to_db(df: pd.DataFrame, table_name: str):
    """SSH 터널을 통해 데이터프레임을 지정된 테이블에 삽입합니다."""
    load_dotenv()

    ssh_host = os.getenv("SSH_HOST")
    ssh_port = int(os.getenv("SSH_PORT"))
    ssh_user = os.getenv("SSH_USER")
    ssh_pkey = os.getenv("SSH_PKEY")

    db_host = os.getenv("DB_HOST")
    db_port = int(os.getenv("DB_PORT"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")

    print(f"\n▶ '{table_name}' 테이블에 데이터 삽입을 시작합니다...")
    try:
        with SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_pkey=ssh_pkey,
                remote_bind_address=(db_host, db_port)
        ) as server:
            local_port = server.local_bind_port
            conn_str = f'mysql+pymysql://{db_user}:{db_password}@127.0.0.1:{local_port}/{db_name}'
            engine = create_engine(conn_str)

            df.to_sql(table_name, con=engine, if_exists='append', index=False)
            print(f"✅ '{table_name}' 테이블에 데이터 {len(df)}건이 성공적으로 삽입되었습니다.")

    except Exception as e:
        print(f"!! 오류: '{table_name}' 테이블 처리 중 문제가 발생했습니다: {e}")

# main 함수와 if __name__ == "__main__": 블록은 여기서 제거합니다.