from io import BytesIO
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from analysis import build_highlight_insights

FONT_PATH = "fonts/NanumGothic.ttf"

pdfmetrics.registerFont(TTFont("NanumGothic", FONT_PATH))

matplotlib.rcParams["font.family"] = "NanumGothic"
matplotlib.rcParams["axes.unicode_minus"] = False

def figure_to_image_data(fig) -> BytesIO:
    '''이 파트는 matplotlib 그래프를 파일 대신 메모리에 담아서 PDF에 넣기 위한 구조'''
    image_buffer = BytesIO()
    '''메모리 속 임시 파일 만들기'''
    fig.savefig(image_buffer, format="png", dpi=150, bbox_inches="tight")
    '''그래프를 진짜 파일이 아니라 메모리 버퍼에 저장'''
    image_buffer.seek(0)
    '''읽기 위치를 맨 앞으로 되돌림. 이거 안 하면 나중에 읽을 때 꼬일 수 있음'''
    plt.close(fig)
    return image_buffer

def make_monthly_chart_image(monthly: pd.DataFrame) -> BytesIO:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(monthly["month"], monthly["sales"])
    ax.set_title("Monthly Sales")
    ax.set_xlabel("month")
    ax.set_ylabel("sales")
    fig.tight_layout()
    return figure_to_image_data(fig)


def make_product_chart_image(product: pd.DataFrame) -> BytesIO:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(product["product"], product["sales"])
    ax.set_title("Product Sales")
    ax.set_xlabel("product")
    ax.set_ylabel("sales")
    plt.xticks(rotation=45)
    fig.tight_layout()
    return figure_to_image_data(fig)

def build_pdf_report(
    industry: str,
    summary_text: str,
    monthly: pd.DataFrame,
    product: pd.DataFrame,
    month_product: pd.DataFrame
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    '''메모리 버퍼 만들고, 거기에 PDF를 그림

    즉 디스크에 바로 저장하는 대신, 메모리에서 PDF를 만든 뒤 bytes로 돌려줌'''

    width, height = A4
    left_margin = 20 * mm
    right_margin = 20 * mm
    usable_width = width - left_margin - right_margin
    top_y = height - 20 * mm
    line_height = 7 * mm

    y = top_y

    # 제목
    c.setFont("NanumGothic", 16)
    c.drawString(left_margin, y, "Sales Report")
    y -= 10 * mm
    '''PDF는 좌표 기반
    문자 하나 쓸 때마다 y를 내려서 다음 줄 위치 잡는 식'''

    c.setFont("NanumGothic", 11)
    c.drawString(left_margin, y, f"Industry: {industry}")
    y -= 10 * mm

    # 핵심 인사이트 박스
    highlight_lines = build_highlight_insights(monthly, product, month_product)

    box_x = left_margin
    box_width = usable_width
    box_height = 45 * mm
    box_y = y - box_height

    c.rect(box_x, box_y, box_width, box_height)
    '''사각형 그림'''

    text_y = box_y + box_height - 8 * mm
    c.setFont("NanumGothic", 12)
    c.drawString(box_x + 5 * mm, text_y, "핵심 인사이트")
    text_y -= 8 * mm

    c.setFont("NanumGothic", 10)
    for line in highlight_lines:
        c.drawString(box_x + 5 * mm, text_y, f"- {line}")
        text_y -= 7 * mm

    y = box_y - 10 * mm

    # 요약 리포트
    c.setFont("NanumGothic", 12)
    c.drawString(left_margin, y, "Summary")
    y -= 8 * mm

    c.setFont("NanumGothic", 10)
    summary_lines = summary_text.split("\n")
    '''문자열을 줄 단위로 나눔'''

    for line in summary_lines:
        if y < 20 * mm:
            c.showPage()
            y = top_y
            '''페이지 밑으로 너무 내려가면 새 페이지 시작
            이건 PDF 작성에서 아주 중요한 패턴'''
            c.setFont("NanumGothic", 10)

        max_chars = 90
        while len(line) > max_chars:
            c.drawString(left_margin, y, line[:max_chars])
            line = line[max_chars:]
            y -= line_height
            if y < 20 * mm:
                c.showPage()
                y = top_y
                c.setFont("NanumGothic", 10)

        c.drawString(left_margin, y, line)
        y -= line_height

    # 새 페이지에서 그래프 시작
    c.showPage()
    y = top_y

    # 월별 그래프
    c.setFont("NanumGothic", 12)
    c.drawString(left_margin, y, "Monthly Sales Chart")
    y -= 10 * mm

    monthly_chart = make_monthly_chart_image(monthly)
    monthly_reader = ImageReader(monthly_chart)
    '''그래프를 메모리 이미지로 만들고
    PDF에 삽입'''
    chart_height = 80 * mm
    c.drawImage(
        monthly_reader,
        left_margin,
        y - chart_height,
        width=usable_width,
        height=chart_height,
        preserveAspectRatio=True,
        mask='auto'
    )
    y -= (chart_height + 15 * mm)

    # 상품별 그래프
    if y < 100 * mm:
        c.showPage()
        y = top_y

    c.setFont("NanumGothic", 12)
    c.drawString(left_margin, y, "Product Sales Chart")
    y -= 10 * mm

    product_chart = make_product_chart_image(product)
    product_reader = ImageReader(product_chart)

    c.drawImage(
        product_reader,
        left_margin,
        y - chart_height,
        width=usable_width,
        height=chart_height,
        preserveAspectRatio=True,
        mask='auto'
    )
    y -= (chart_height + 15 * mm)

    # 월별 매출 텍스트
    if y < 50 * mm:
        c.showPage()
        y = top_y

    c.setFont("NanumGothic", 12)
    c.drawString(left_margin, y, "Monthly Sales")
    y -= 8 * mm

    c.setFont("NanumGothic", 10)
    for _, row in monthly.iterrows():
        line = f'{int(row["month"])} month : {float(row["sales"]):,.0f}'
        c.drawString(left_margin, y, line)
        y -= line_height

        if y < 20 * mm:
            c.showPage()
            y = top_y
            c.setFont("NanumGothic", 10)

    y -= 5 * mm

    # 상품별 매출 텍스트
    if y < 50 * mm:
        c.showPage()
        y = top_y

    c.setFont("NanumGothic", 12)
    c.drawString(left_margin, y, "Product Sales")
    y -= 8 * mm

    c.setFont("NanumGothic", 10)
    for _, row in product.iterrows():
        line = f'{row["product"]} : {float(row["sales"]):,.0f}'
        c.drawString(left_margin, y, line)
        y -= line_height

        if y < 20 * mm:
            c.showPage()
            y = top_y
            c.setFont("NanumGothic", 10)

    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
'''PDF 작성 완료 후 bytes 형태로 꺼냄
이게 Streamlit 다운로드 버튼에 들어가는 데이터가 됨'''