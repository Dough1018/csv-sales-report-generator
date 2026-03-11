import streamlit as st
import pandas as pd

from analysis import (
    validate_dataframe,
    make_aggregates,
    build_industry_summary,
    make_month_from_date_column
)
from pdf_report import build_pdf_report
from ui import render_analysis_result


def analyze_and_render(industry, df):
    monthly, product, month_product = make_aggregates(df)

    final_summary = build_industry_summary(
        industry, df, monthly, product, month_product
    )

    pdf_data = build_pdf_report(
        industry, final_summary, monthly, product, month_product
    )

    render_analysis_result(
        industry=industry,
        final_summary=final_summary,
        monthly=monthly,
        product=product,
        month_product=month_product,
        pdf_data=pdf_data
    )


st.title("업종별 CSV 리포트 생성기")

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

        columns = list(raw_df.columns)

        month_input_type = st.radio(
            "월 정보를 어떻게 가져올까요?",
            ["월 컬럼 직접 선택", "날짜 컬럼에서 월 자동 추출"]
        )

        if month_input_type == "월 컬럼 직접 선택":
            month_col = st.selectbox("month에 해당하는 컬럼", columns)
            date_col = None
        else:
            date_col = st.selectbox("날짜에 해당하는 컬럼", columns)
            month_col = None

        product_col = st.selectbox("product에 해당하는 컬럼", columns)
        sales_col = st.selectbox("sales에 해당하는 컬럼", columns)

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

                analyze_and_render(industry, df)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")