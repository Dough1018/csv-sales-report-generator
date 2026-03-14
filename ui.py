import streamlit as st
import matplotlib.pyplot as plt


def render_monthly_chart(monthly):
    st.subheader("월별 매출 그래프")
    fig, ax = plt.subplots()
    ax.plot(monthly["month"], monthly["sales"])
    ax.set_xlabel("month")
    ax.set_ylabel("sales")
    st.pyplot(fig)


def render_product_chart(product):
    st.subheader("상품별 매출 그래프")
    fig, ax = plt.subplots()
    ax.bar(product["product"], product["sales"])
    ax.set_xlabel("product")
    ax.set_ylabel("sales")
    plt.xticks(rotation=45)
    st.pyplot(fig)


def render_download_buttons(final_summary, monthly, product, month_product, pdf_data):
    st.download_button(
        label="요약 리포트 다운로드",
        data=final_summary,
        file_name="summary.txt",
        mime="text/plain"
    )

    st.download_button(
        label="PDF 리포트 다운로드",
        data=pdf_data,
        file_name="sales_report.pdf",
        mime="application/pdf"
    )

    monthly_csv = monthly.to_csv(index=False).encode("utf-8-sig")
    product_csv = product.to_csv(index=False).encode("utf-8-sig")
    month_product_csv = month_product.to_csv(index=False).encode("utf-8-sig")

    st.subheader("분석 결과 CSV 다운로드")

    st.download_button(
        label="월별 매출 CSV 다운로드",
        data=monthly_csv,
        file_name="monthly_sales.csv",
        mime="text/csv"
    )

    st.download_button(
        label="상품별 매출 CSV 다운로드",
        data=product_csv,
        file_name="product_sales.csv",
        mime="text/csv"
    )

    st.download_button(
        label="월별+상품별 매출 CSV 다운로드",
        data=month_product_csv,
        file_name="month_product_sales.csv",
        mime="text/csv"
    )


def render_tables(monthly, product, month_product):
    st.subheader("월별 매출")
    st.dataframe(monthly)

    st.subheader("상품별 매출")
    st.dataframe(product)

    st.subheader("월별 + 상품별 매출")
    st.dataframe(month_product)


def render_analysis_result(industry, final_summary, monthly, product, month_product, pdf_data, ai_comment):
    st.success("분석 완료!")

    st.subheader("선택한 업종")
    st.write(industry)

    st.subheader("AI 매출 분석 코멘트")
    st.info(ai_comment)

    st.subheader("요약 리포트")
    st.text(final_summary)

    render_download_buttons(final_summary, monthly, product, month_product, pdf_data)
    render_tables(monthly, product, month_product)
    render_monthly_chart(monthly)
    render_product_chart(product)