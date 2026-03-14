import streamlit as st
import pandas as pd

from analysis import (
    validate_dataframe,
    make_aggregates,
    build_industry_summary,
    make_month_from_date_column,
    guess_column_mapping
)
from pdf_report import build_pdf_report
from ui import render_analysis_result

from ai_commentary import build_ai_sales_comment


def analyze_and_render(industry, df):
    monthly, product, month_product = make_aggregates(df)

    final_summary = build_industry_summary(
        industry, df, monthly, product, month_product
    )

    ai_comment = build_ai_sales_comment(final_summary, industry)

    pdf_data = build_pdf_report(
        industry, final_summary, monthly, product, month_product
    )

    render_analysis_result(
        industry=industry,
        final_summary=final_summary,
        monthly=monthly,
        product=product,
        month_product=month_product,
        pdf_data=pdf_data,
        ai_comment=ai_comment
    )


st.title("업종별 CSV 리포트 생성기")

st.caption("CSV 데이터를 업로드하면 자동으로 매출 분석 리포트와 PDF 보고서를 생성합니다.")

st.markdown("""
### 사용 방법
1. CSV 파일 업로드
2. 컬럼 매핑
3. 분석 결과 확인
4. PDF 또는 CSV 다운로드
""")

sample_csv = """month,product,sales
1,Americano,120000
1,Latte,95000
2,Americano,150000
2,Latte,100000
"""

st.download_button(
    label="샘플 CSV 다운로드",
    data=sample_csv,
    file_name="sample_sales.csv",
    mime="text/csv"
)

industry = st.radio(
    "업종을 선택하세요:",
    ["일반 매출", "카페", "식당"]
)

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    try:
        raw_df = pd.read_csv(uploaded_file)

        st.subheader("업로드한 CSV 미리보기")
        st.dataframe(raw_df.head())

        st.subheader("컬럼 매핑")
        st.write("CSV 안의 실제 컬럼을 분석용 컬럼에 연결하세요.")
        st.info("컬럼을 자동으로 추측해 기본 선택해두었습니다. 필요하면 직접 바꿔주세요.")

        columns = list(raw_df.columns)
        guessed = guess_column_mapping(columns)

        default_month_input_type_index = 0
        if guessed["month_col"] is None and guessed["date_col"] is not None:
            default_month_input_type_index = 1

        month_input_type = st.radio(
            "월 정보를 어떻게 가져올까요?",
            ["월 컬럼 직접 선택", "날짜 컬럼에서 월 자동 추출"],
            index=default_month_input_type_index
        )

        if month_input_type == "월 컬럼 직접 선택":
            default_month_index = 0
            if guessed["month_col"] in columns:
                default_month_index = columns.index(guessed["month_col"])

            month_col = st.selectbox(
                "month에 해당하는 컬럼",
                columns,
                index=default_month_index
            )
            date_col = None
        else:
            default_date_index = 0
            if guessed["date_col"] in columns:
                default_date_index = columns.index(guessed["date_col"])

            date_col = st.selectbox(
                "날짜에 해당하는 컬럼",
                columns,
                index=default_date_index
            )
            month_col = None

        default_product_index = 0
        if guessed["product_col"] in columns:
            default_product_index = columns.index(guessed["product_col"])

        default_sales_index = 0
        if guessed["sales_col"] in columns:
            default_sales_index = columns.index(guessed["sales_col"])

        product_col = st.selectbox(
            "product에 해당하는 컬럼",
            columns,
            index=default_product_index
        )

        sales_col = st.selectbox(
            "sales에 해당하는 컬럼",
            columns,
            index=default_sales_index
        )

        if month_input_type == "월 컬럼 직접 선택":
            selected_cols = [month_col, product_col, sales_col]

            if len(set(selected_cols)) < 3:
                st.warning("month / product / sales는 서로 다른 컬럼을 선택해야 합니다.")
            else:
                df = raw_df.rename(columns={
                    month_col: "month",
                    product_col: "product",
                    sales_col: "sales"
                })

                df = df[["month", "product", "sales"]]
                df = validate_dataframe(df)

                with st.spinner("데이터 분석 중입니다..."):
                    analyze_and_render(industry, df)

        else:
            selected_cols = [date_col, product_col, sales_col]

            if len(set(selected_cols)) < 3:
                st.warning("날짜 / product / sales는 서로 다른 컬럼을 선택해야 합니다.")
            else:
                df = raw_df.copy()
                df["month"] = make_month_from_date_column(df, date_col)
                df = df.rename(columns={
                    product_col: "product",
                    sales_col: "sales"
                })

                df = df[["month", "product", "sales"]]
                df = validate_dataframe(df)

                with st.spinner("데이터 분석 중입니다..."):
                    analyze_and_render(industry, df)

    except Exception as e:
        st.error("CSV 파일 형식 또는 데이터 내용을 확인해주세요.")
        st.error(str(e))