CSV Sales Report Generator

CSV 매출 데이터를 업로드하면 자동으로 분석하고
요약 리포트, 그래프, PDF 보고서를 생성하는 Streamlit 웹 애플리케이션입니다.

이 프로젝트는 소상공인 / 매출 데이터 자동 분석 도구를 목표로 만들어졌습니다.

Demo

Streamlit 웹앱

https://csv-sales-report-generator.streamlit.app

주요 기능

1️⃣ CSV 업로드 분석

사용자가 CSV 파일을 업로드하면 자동으로 데이터를 분석합니다.

2️⃣ 컬럼 매핑 기능

CSV 구조가 달라도 분석 가능하도록

사용자가 직접 컬럼을 연결할 수 있습니다.

예:

month
product
sales

또는

date → month 자동 변환
3️⃣ 날짜 컬럼 자동 월 변환

날짜 데이터가 있는 경우

2024-01-12
2024-02-03

이런 형식에서 자동으로

1월
2월

로 변환하여 분석합니다.

4️⃣ 매출 분석

자동으로 다음 데이터를 계산합니다.

월별 매출

상품별 매출

월 + 상품 매출

5️⃣ 자동 인사이트 생성

데이터를 기반으로 자동 코멘트를 생성합니다.

예:

최고 매출 월

최저 매출 월

가장 성장한 상품

가장 하락한 상품

6️⃣ 그래프 자동 생성

Streamlit + matplotlib 기반

월별 매출 그래프

상품 매출 그래프

7️⃣ PDF 리포트 생성

ReportLab 기반으로

다음 내용이 포함된 PDF 리포트를 생성합니다.

핵심 인사이트

매출 요약

그래프

상품별 매출

8️⃣ CSV 결과 다운로드

분석 결과를 CSV로 다운로드할 수 있습니다.

monthly_sales.csv

product_sales.csv

month_product_sales.csv

사용 기술

Python

pandas

Streamlit

matplotlib

ReportLab

프로젝트 구조
csv-sales-report-generator

│

├ app.py

├ analysis.py

├ ui.py

├ pdf_report.py

├ requirements.txt

│

└ fonts

    └ NanumGothic.ttf
    
실행 방법

1️⃣ 저장소 클론

git clone https://github.com/your-id/csv-sales-report-generator
2️⃣ 패키지 설치

pip install -r requirements.txt

3️⃣ 실행

streamlit run app.py

예시 CSV 구조

month,product,sales

1,Americano,120000

1,Latte,95000

2,Americano,150000

2,Latte,100000

또는

date,product,sales

2024-01-03,Americano,120000

2024-01-05,Latte,95000


향후 개선 계획

업종별 분석 확장

더 정교한 인사이트 분석

CSV 자동 컬럼 인식

AI 기반 매출 코멘트 생성

SaaS 형태 서비스 확장

라이선스

MIT License

제작자

GitHub

https://github.com/Dough1018
