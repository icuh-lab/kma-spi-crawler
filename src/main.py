import os
import time
import pandas as pd
import crawler  # 크롤링 기능 모듈
import csv_to_db  # DB 처리 기능 모듈
from datetime import date, timedelta  # 날짜 계산을 위해 import 추가


def main():
    """
    메인 실행 함수: 데이터 수집부터 DB 적재까지 전체 프로세스를 관리합니다.
    """
    # --- 1. 설정 값 ---
    URL = "https://data.kma.go.kr/data/gaw/selectSpiRltmList.do?pgmNo=734"

    target_date = date.today() - timedelta(days=2)
    START_DATE = target_date.strftime("%Y%m%d")
    END_DATE = target_date.strftime("%Y%m%d")

    print(f"▶ 동적으로 설정된 날짜: {START_DATE}")

    REGIONS_TO_EXPAND = ["강원특별자치도", "경상남도", "대전광역시", "충청북도"]
    LOCATIONS_TO_SELECT = ["춘천 (101)", "합천 (285)", "대전 (133)", "충주 (127)"]
    SPI_ELEMENTS_TO_SELECT = ["SPI1", "SPI2", "SPI3", "SPI4", "SPI5", "SPI6", "SPI9", "SPI12", "SPI18", "SPI24"]

    # 지점 ID와 DB 테이블 이름 매핑
    STATION_TABLE_MAP = {
        101: 'drought_impact_chuncheon_spi_index',
        127: 'drought_impact_chungju_spi_index',
        133: 'drought_impact_daejeon_spi_index',
        285: 'drought_impact_hapcheon_spi_index'
    }

    # 다운로드 폴더 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    DOWNLOAD_DIR = os.path.join(project_root, "output")

    # --- 2. 크롤링 및 다운로드 실행 ---
    driver = None
    try:
        driver, wait = crawler.setup_driver(DOWNLOAD_DIR)
        driver.get(URL)
        crawler.set_dates(driver, wait, START_DATE, END_DATE)
        crawler.select_locations(driver, wait, REGIONS_TO_EXPAND, LOCATIONS_TO_SELECT)
        crawler.select_elements(driver, wait, SPI_ELEMENTS_TO_SELECT)
        crawler.search_and_download(driver, wait)

        print("\n▶ 파일 다운로드를 20초 동안 기다립니다...")
        time.sleep(20)
        print("🎉 파일 다운로드 완료!")
    except Exception as e:
        print(f"\n크롤링 중 오류가 발생했습니다: {e}")
    finally:
        if driver:
            driver.quit()
            print("\n▶ 브라우저를 종료합니다.")

    # --- 3. 다운로드된 파일 DB에 적재 ---
    print("\n========================================")
    print("▶ 데이터베이스 적재를 시작합니다...")
    print("========================================")

    latest_csv = csv_to_db.find_latest_csv_file(DOWNLOAD_DIR)

    if latest_csv:
        try:
            raw_df = pd.read_csv(latest_csv, encoding='cp949')
            transformed_df = csv_to_db.transform_dataframe(raw_df)

            for station_id, table_name in STATION_TABLE_MAP.items():
                station_df = transformed_df[transformed_df['station_id'] == station_id].copy()
                if not station_df.empty:
                    csv_to_db.insert_data_to_db(station_df, table_name)
                else:
                    print(f"\n- 정보: station_id {station_id}에 해당하는 데이터가 CSV 파일에 없습니다.")

            print("\n🎉 모든 DB 작업이 성공적으로 완료되었습니다!")
        except Exception as e:
            print(f"\n!! DB 적재 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()