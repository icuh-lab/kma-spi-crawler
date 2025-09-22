import time
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def setup_driver(download_dir):
    """다운로드 폴더 설정 및 웹 드라이버를 초기화합니다."""
    env = os.getenv("EXECUTION_ENV", "local")
    print(f"--- 실행 환경: {env} ---")

    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }

    chrome_options.add_experimental_option("prefs", prefs)

    if env == "production":
        print("운영 환경으로 판단하여 RDS에 직접 접속합니다.(Headless 모드)")

        # --- 서버 환경을 위한 옵션 추가 ---
        chrome_options.add_argument("--headless")  # GUI 없이 백그라운드에서 실행
        chrome_options.add_argument("--no-sandbox")  # Docker 컨테이너 환경에서 필수
        chrome_options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 관련 문제 방지
        chrome_options.add_argument("--window-size=1920x1080")  # 창 크기 설정 (레이아웃 깨짐 방지)
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")  # 일반적인 사용자처럼 보이게 설정
    else:
        print("로컬 환경으로 드라이버 옵션을 설정합니다.")

    # 드라이버와 wait 객체 생성 (중복 제거)
    driver = webdriver.Chrome(options=chrome_options)

    # 로컬 환경에서만 창 최대화
    if env != "production":
        driver.maximize_window()

    wait = WebDriverWait(driver, 20)
    print("▶ 웹 드라이버가 성공적으로 설정되었습니다.")

    return driver, wait


def set_dates(driver, wait, start_date, end_date):
    """웹사이트에서 시작일과 종료일을 설정합니다."""
    print(f"\n▶ 기간 설정: {start_date} ~ {end_date}")
    try:
        start_input = wait.until(EC.presence_of_element_located((By.ID, "startDt_d")))
        end_input = driver.find_element(By.ID, "endDt_d")
        start_input.clear()
        start_input.send_keys(start_date)
        end_input.clear()
        end_input.send_keys(end_date)
        time.sleep(1)
    except TimeoutException:
        print("  - 오류: 날짜 입력 필드를 찾지 못했습니다.")


def select_locations(driver, wait, regions, locations):
    """지정된 지역 및 지점을 선택합니다."""
    print("\n▶ 지점 선택 중...")
    for region in regions:
        try:
            xpath = f"//a[contains(@id, '_a') and ./label[text()='{region}']]//preceding-sibling::a[contains(@id, '_switch')]"
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            if 'close' in button.get_attribute('class'):
                button.click()
                time.sleep(0.5)
        except TimeoutException:
            print(f"  - 경고: '{region}' 지역을 펼칠 수 없습니다.")

    for location in locations:
        try:
            xpath = f"//label[text()='{location}']/parent::a/preceding-sibling::a[contains(@id, '_check')]"
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(0.1)
        except TimeoutException:
            print(f"  - 경고: '{location}' 지점을 찾을 수 없습니다.")
    print("  - 지점 선택 완료.")


def select_elements(driver, wait, elements):
    """지정된 요소를 선택합니다."""
    print("\n▶ 요소 선택 중...")
    try:
        parent_xpath = "//label[text()='표준강수지수']/parent::a/preceding-sibling::a[contains(@id, '_switch')]"
        parent_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, parent_xpath)))
        if 'close' in parent_toggle.get_attribute('class'):
            parent_toggle.click()
            time.sleep(0.5)
    except TimeoutException:
        print("  - 경고: '표준강수지수' 목록을 펼칠 수 없습니다.")

    for element in elements:
        try:
            xpath = f"//label[text()='{element}']/parent::a/preceding-sibling::a[contains(@id, '_check')]"
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(0.1)
        except TimeoutException:
            print(f"  - 경고: '{element}' 요소를 찾을 수 없습니다.")
    print("  - 요소 선택 완료.")


def search_and_download(driver, wait):
    """'조회' 및 'CSV 다운로드' 관련 버튼들을 차례로 클릭합니다."""
    print("\n▶ 조회 및 다운로드 요청...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '조 회')]"))).click()
    time.sleep(5)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='btn_file' and text()='CSV']"))).click()
    confirm_xpath = "//div[@id='loginPop']//a[@class='btn_gray' and text()='확인']"
    wait.until(EC.element_to_be_clickable((By.XPATH, confirm_xpath))).click()
    print("  - 다운로드 요청 완료.")