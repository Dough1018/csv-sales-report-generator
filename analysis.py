import os
from typing import Tuple
import pandas as pd

REQUIRED_COLUMNS = {"month", "product", "sales"}

def validate_and_load(csv_source) -> pd.DataFrame:
    '''반환 타입 힌트
“이 함수는 최종적으로 pandas DataFrame을 돌려줍니다” 라는 뜻'''
    if isinstance(csv_source, str):
        '''isinstance “이 값이 특정 타입인지 확인하는 함수”
        즉: csv_source가 문자열이면 그 문자열이 파일 경로일 가능성이 크니까 파일이 실제로 존재하는지 확인
        아래껀 일부러 에러를 발생시킨다는 의미'''
        if not os.path.exists(csv_source):
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {csv_source}")

    df = pd.read_csv(csv_source)
    return validate_dataframe(df)

def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    '''df.columns : 데이터프레임의 컬럼 이름 목록'''
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {sorted(missing)} / 현재 컬럼: {list(df.columns)}")
    '''sorted(missing) = 빠진 컬럼 정렬, list(df.columns) = 현재 컬럼 보기 쉽게 리스트로 변환'''

    df = df.copy()
    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    '''pd.to_numeric : 문자열이든 뭐든 숫자로 바꾸려는 함수
    errors="coerce" : 변환 실패하면 에러 내지 말고 NaN으로 바꿔라'''
    df["product"] = df["product"].astype(str)

    df = df.dropna(subset=["month", "product", "sales"])
    '''month/product/sales 중 하나라도 비어 있으면 그 행을 지워버리는 거'''
    df["month"] = df["month"].astype(int)

    if df.empty:
        raise ValueError("유효한 데이터가 없습니다. month/product/sales 값을 확인하세요.")

    return df

def make_month_from_date_column(df: pd.DataFrame, date_col: str) -> pd.Series:
    date_series = pd.to_datetime(df[date_col], errors="coerce")
    month_series = date_series.dt.month

    if month_series.dropna().empty:
        raise ValueError(f"날짜 컬럼 '{date_col}'에서 월 정보를 추출할 수 없습니다.")

    return month_series

def make_aggregates(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    '''이 함수는 집계 결과 3개를 반환 monthly product month_product
    즉 “원본 데이터 하나를 넣으면, 분석용 요약표 세 개를 만들어줌”'''
    monthly = (
        df.groupby("month", as_index=False)["sales"]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )

    product = (
        df.groupby("product", as_index=False)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
        .reset_index(drop=True)
    )

    month_product = (
        df.groupby(["month", "product"], as_index=False)["sales"]
        .sum()
        .sort_values(["month", "sales"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return monthly, product, month_product

'''
build_industry_summary()는 문지기 함수

이 함수는 직접 긴 계산을 많이 하진 않음
대신 “누구를 부를지 결정”
'''
def build_summary(
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    product: pd.DataFrame,
    month_product: pd.DataFrame
) -> str:
    total_sales = float(df["sales"].sum())
    avg_row_sales = float(df["sales"].mean())
    avg_month_sales = monthly["sales"].mean()

    # Top 1
    best_product = str(product.iloc[0]["product"])
    best_product_sales = float(product.iloc[0]["sales"])
    best_share = (best_product_sales / total_sales * 100.0) if total_sales != 0 else 0.0

    # Top 2 (데이터가 2개 상품 이상일 때)
    if len(product) >= 2:
        second_product = str(product.iloc[1]["product"])
        second_product_sales = float(product.iloc[1]["sales"])
        second_share = (second_product_sales / total_sales * 100.0) if total_sales != 0 else 0.0
    else:
        second_product = "N/A"
        second_product_sales = 0.0
        second_share = 0.0

    share_gap_pp = best_share - second_share  # percentage points

    # 월별 매출 텍스트
    monthly_pairs = [f'{int(r["month"])}월 {float(r["sales"]):,.0f}' for _, r in monthly.iterrows()]
    '''f'...' : 문자열 포맷팅
    monthly.iterrows() : 행을 하나씩 꺼내옴
    for _, r in ... : 각 행을 반복'''
    monthly_text = ", ".join(monthly_pairs)
    ''' ", ".join(monthly_pairs) : 리스트를 쉼표로 이어붙임
    ["1월 100,000", "2월 120,000"] → "1월 100,000, 2월 120,000"'''

    # 전월 대비
    mom_text = "전월 대비: 데이터가 2개월 이상이면 계산합니다."
    if len(monthly) >= 2:
        last = float(monthly.iloc[-1]["sales"])
        '''iloc[-1] 마지막 행'''
        prev = float(monthly.iloc[-2]["sales"])
        if prev == 0:
            mom_text = f"전월 대비: 이전 달 매출이 0이라 증감률 계산 불가 (이전={prev:,.0f}, 최근={last:,.0f})."
        else:
            diff = last - prev
            rate = (diff / prev) * 100.0
            direction = "증가" if diff >= 0 else "감소"
            mom_text = f"전월 대비: 최근 달 매출이 {direction} ({diff:+.0f}, {rate:+.1f}%)."

    # 최고 매출 월
    top_month_row = monthly.sort_values("sales", ascending=False).iloc[0]
    top_month = int(top_month_row["month"])
    top_month_sales = float(top_month_row["sales"])

    low_month_row = monthly.sort_values("sales", ascending=True).iloc[0]
    low_month = int(low_month_row["month"])
    low_month_sales = float(low_month_row["sales"])

    # 매출변동폭
    top_low_gap = top_month_sales - low_month_sales

    # 편중도 레이블(간단 규칙)
    if best_share >= 70:
        concentration = "높음"
    elif best_share >= 55:
        concentration = "중간"
    else:
        concentration = "낮음"

    lines = []
    '''문자열을 하나하나 이어붙이기보다, 먼저 리스트에 문장을 모아두고
    마지막에 "\n".join(lines)로 줄바꿈 붙여서 하나의 문자열로 만드는 방식'''
    lines.append("=== 매출 리포트 요약(v1.2) ===")
    lines.append(f"- 총 매출: {total_sales:,.0f}")
    lines.append(f"- 평균 매출(행 기준): {avg_row_sales:,.1f}")
    lines.append(f"- 월별 매출: {monthly_text}")
    lines.append(f"- 베스트 상품: {best_product} (총 {best_product_sales:,.0f}, 비중 {best_share:.1f}%)")
    if second_product != "N/A":
        lines.append(f"- 2위 상품: {second_product} (총 {second_product_sales:,.0f}, 비중 {second_share:.1f}%)")
        lines.append(f"- Top1-Top2 비중 격차: {share_gap_pp:.1f}%p (편중도: {concentration})")
    lines.append(f"- 최고 매출 월: {top_month}월 (총 {top_month_sales:,.0f})")
    lines.append(f"- 최저 매출 월: {low_month}월 (총 {low_month_sales:,.0f})")
    lines.append(f"- 월 평균 매출: {avg_month_sales:.1f}")
    lines.append(f"- 월 매출 변동 폭: {top_low_gap:,.0f} (최고 {top_month_sales:,.0f} - 최저 {low_month_sales:,.0f})")
    lines.append(f"- {mom_text}")
    lines.append("")
    lines.append("추천 액션(자동 생성):")
    lines.append(f"1) {best_product} 비중이 {best_share:.1f}% (편중도 {concentration})입니다. 재고/노출/프로모션 우선순위를 먼저 점검하세요.")
    if second_product != "N/A":
        lines.append(f"2) 2위 상품({second_product}) 비중은 {second_share:.1f}%입니다. {second_product} 단독 프로모션/노출 테스트로 의존도를 분산해보세요.")
    lines.append("3) 월별/상품별 그래프를 매월 저장하면 '갑자기 떨어진 달'을 빠르게 발견할 수 있습니다.")

    insight_lines = build_insight_lines(monthly, product)
    lines.extend(insight_lines)

    product_trend_lines = build_product_trend_lines(month_product)
    lines.extend(product_trend_lines)

    return "\n".join(lines)

def build_cafe_summary(
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    product: pd.DataFrame,
    month_product: pd.DataFrame
) -> str:
    base_summary = build_summary(df, monthly, product, month_product)

    total_sales = float(df["sales"].sum())
    best_product = str(product.iloc[0]["product"])
    best_product_sales = float(product.iloc[0]["sales"])
    best_share = (best_product_sales / total_sales * 100) if total_sales != 0 else 0

    lines = []
    lines.append("")
    lines.append("=== 카페 업종 추가 코멘트 ===")
    lines.append(f"- 대표 음료/메뉴 후보: {best_product}")
    lines.append(f"- 대표 메뉴 매출 비중: {best_share:.1f}%")

    if best_share >= 50:
        lines.append("- 특정 메뉴 쏠림이 큰 편입니다. 대표 메뉴 품절, 원가, 리뷰 관리를 우선 점검해보세요.")
    else:
        lines.append("- 메뉴 매출이 비교적 분산되어 있습니다. 세트 메뉴나 추가 주문 유도로 객단가를 높여볼 수 있습니다.")

    if len(product) >= 2:
        second_product = str(product.iloc[1]["product"])
        second_product_sales = float(product.iloc[1]["sales"])
        second_share = (second_product_sales / total_sales * 100) if total_sales != 0 else 0

        lines.append(f"- 2위 메뉴는 {second_product} ({second_share:.1f}%)입니다.")
        lines.append("- 상위 2개 메뉴를 묶은 세트/추천 조합 테스트가 잘 맞을 수 있습니다.")

    if len(monthly) >= 2:
        last = float(monthly.iloc[-1]["sales"])
        prev = float(monthly.iloc[-2]["sales"])

        if prev != 0:
            rate = ((last - prev) / prev) * 100
            if rate > 0:
                lines.append("- 최근 월 매출이 상승 중입니다. 인기 메뉴 중심 리뷰 확보/재방문 쿠폰을 붙여볼 만합니다.")
            else:
                lines.append("- 최근 월 매출이 둔화되었습니다. 시즌 메뉴, 재방문 할인, 배달앱 프로모션을 검토해보세요.")

    return base_summary + "\n" + "\n".join(lines)


def build_restaurant_summary(
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    product: pd.DataFrame,
    month_product: pd.DataFrame
) -> str:
    base_summary = build_summary(df, monthly, product, month_product)

    total_sales = float(df["sales"].sum())
    best_product = str(product.iloc[0]["product"])
    best_product_sales = float(product.iloc[0]["sales"])
    best_share = (best_product_sales / total_sales * 100) if total_sales != 0 else 0

    lines = []
    lines.append("")
    lines.append("=== 식당 업종 추가 코멘트 ===")
    lines.append(f"- 주력 메뉴 후보: {best_product}")
    lines.append(f"- 주력 메뉴 매출 비중: {best_share:.1f}%")

    if best_share >= 55:
        lines.append("- 특정 메뉴 의존도가 높습니다. 주력 메뉴 품질 유지와 함께 사이드/세트 확장이 중요합니다.")
    else:
        lines.append("- 여러 메뉴가 고르게 판매되고 있습니다. 베스트 메뉴 조합으로 세트 메뉴를 설계해보기 좋습니다.")

    if len(product) >= 2:
        second_product = str(product.iloc[1]["product"])
        second_product_sales = float(product.iloc[1]["sales"])
        second_share = (second_product_sales / total_sales * 100) if total_sales != 0 else 0

        lines.append(f"- 2위 메뉴는 {second_product} ({second_share:.1f}%)입니다.")
        lines.append("- 1위/2위 메뉴를 중심으로 대표 세트, 점심 특선, 저녁 추천 구성을 실험해볼 수 있습니다.")

    top_month_row = monthly.sort_values("sales", ascending=False).iloc[0]
    low_month_row = monthly.sort_values("sales", ascending=True).iloc[0]
    top_month = int(top_month_row["month"])
    low_month = int(low_month_row["month"])

    lines.append(f"- 가장 강한 달은 {top_month}월, 가장 약한 달은 {low_month}월입니다.")
    lines.append("- 약한 달에는 할인 행사, 리뷰 이벤트, 배달 전용 메뉴를 붙이는 전략이 유효할 수 있습니다.")

    if len(monthly) >= 2:
        last = float(monthly.iloc[-1]["sales"])
        prev = float(monthly.iloc[-2]["sales"])

        if prev != 0:
            rate = ((last - prev) / prev) * 100
            if rate > 0:
                lines.append("- 최근 매출 흐름이 좋아지고 있습니다. 회전이 좋은 메뉴를 중심으로 객단가 상승 전략을 붙여보세요.")
            else:
                lines.append("- 최근 매출 흐름이 약해졌습니다. 점심 특선, 저녁 세트, 배달 할인 같은 구분 전략을 고민해볼 수 있습니다.")

    return base_summary + "\n" + "\n".join(lines)


def build_industry_summary(
    industry: str,
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    product: pd.DataFrame,
    month_product: pd.DataFrame
) -> str:
    if industry == "일반 매출":
        return build_summary(df, monthly, product, month_product)
    elif industry == "카페":
        return build_cafe_summary(df, monthly, product, month_product)
    elif industry == "식당":
        return build_restaurant_summary(df, monthly, product, month_product)
    else:
        return build_summary(df, monthly, product, month_product)

def build_insight_lines(monthly: pd.DataFrame, product: pd.DataFrame) -> list[str]:
    lines = []
    lines.append("")
    lines.append("=== 자동 인사이트 ===")

    # 월 최고/최저
    top_month_row = monthly.sort_values("sales", ascending=False).iloc[0]
    low_month_row = monthly.sort_values("sales", ascending=True).iloc[0]

    top_month = int(top_month_row["month"])
    top_month_sales = float(top_month_row["sales"])
    low_month = int(low_month_row["month"])
    low_month_sales = float(low_month_row["sales"])

    lines.append(f"- 최고 매출 월은 {top_month}월 ({top_month_sales:,.0f})입니다.")
    lines.append(f"- 최저 매출 월은 {low_month}월 ({low_month_sales:,.0f})입니다.")

    # 전월 대비 증감 계산
    if len(monthly) >= 2:
        monthly_with_diff = monthly.copy()
        monthly_with_diff["diff"] = monthly_with_diff["sales"].diff()
        '''.diff() : 바로 전 행과의 차이를 계산함'''

        # 첫 행은 diff가 NaN 이므로 제외
        diff_rows = monthly_with_diff.dropna(subset=["diff"])

        if not diff_rows.empty:
            best_up_row = diff_rows.sort_values("diff", ascending=False).iloc[0]
            worst_down_row = diff_rows.sort_values("diff", ascending=True).iloc[0]
            '''diff 큰 순 첫 번째 = 가장 많이 오른 달
            diff 작은 순 첫 번째 = 가장 많이 떨어진 달'''

            up_month = int(best_up_row["month"])
            up_diff = float(best_up_row["diff"])

            down_month = int(worst_down_row["month"])
            down_diff = float(worst_down_row["diff"])

            lines.append(f"- 가장 큰 매출 상승은 {up_month}월에 발생했습니다 ({up_diff:+,.0f}).")
            lines.append(f"- 가장 큰 매출 하락은 {down_month}월에 발생했습니다 ({down_diff:+,.0f}).")

            if up_diff > 0:
                lines.append("- 상승 폭이 큰 달의 전후 프로모션/상품 구성을 다시 확인해보면 좋은 힌트를 얻을 수 있습니다.")
            if down_diff < 0:
                lines.append("- 하락 폭이 큰 달은 이벤트 종료, 계절성, 재고 문제 여부를 점검해보는 것이 좋습니다.")

    # 상품 인사이트
    best_product_row = product.iloc[0]
    best_product = str(best_product_row["product"])
    best_product_sales = float(best_product_row["sales"])

    lines.append(f"- 가장 매출이 높은 상품은 {best_product} ({best_product_sales:,.0f})입니다.")

    if len(product) >= 2:
        low_product_row = product.sort_values("sales", ascending=True).iloc[0]
        low_product = str(low_product_row["product"])
        low_product_sales = float(low_product_row["sales"])

        lines.append(f"- 가장 매출이 낮은 상품은 {low_product} ({low_product_sales:,.0f})입니다.")
        lines.append("- 하위 상품은 제거보다 먼저 노출 방식, 묶음 판매, 가격 구성을 테스트해볼 수 있습니다.")

    return lines

def build_product_trend_lines(month_product: pd.DataFrame) -> list[str]:
    lines = []
    lines.append("")
    lines.append("=== 상품 성장/하락 탐지 ===")

    if month_product.empty:
        lines.append("- 상품 추세를 분석할 데이터가 없습니다.")
        return lines

    trend_rows = []

    for product_name, group in month_product.groupby("product"):
        '''상품별로 데이터를 묶어서 각 상품의 월별 흐름을 따로 본다'''
        group = group.sort_values("month").reset_index(drop=True)

        if len(group) >= 2:
            last_sales = float(group.iloc[-1]["sales"])
            prev_sales = float(group.iloc[-2]["sales"])
            diff = last_sales - prev_sales

            trend_rows.append({
                "product": product_name,
                "prev_sales": prev_sales,
                "last_sales": last_sales,
                "diff": diff
            })
            '''
            이건 딕셔너리를 리스트에 넣는 것. 즉 나중에 이런 표를 만들기 위한 중간 재료
            product     prev_sales  last_sales  diff
            ----------------------------------------
            '''

    if not trend_rows:
        lines.append("- 2개월 이상 데이터가 있는 상품이 없어 성장/하락 분석을 건너뜁니다.")
        return lines

    trend_df = pd.DataFrame(trend_rows)
    '''리스트 안의 딕셔너리들을 표로 바꿔줌'''

    best_growth_row = trend_df.sort_values("diff", ascending=False).iloc[0]
    worst_decline_row = trend_df.sort_values("diff", ascending=True).iloc[0]

    best_growth_product = str(best_growth_row["product"])
    best_growth_diff = float(best_growth_row["diff"])

    worst_decline_product = str(worst_decline_row["product"])
    worst_decline_diff = float(worst_decline_row["diff"])

    if best_growth_diff > 0:
        lines.append(f"- 최근 가장 많이 성장한 상품은 {best_growth_product} ({best_growth_diff:+,.0f})입니다.")
        lines.append("- 성장 상품은 노출 확대, 리뷰 확보, 재고 우선 확보 후보로 볼 수 있습니다.")
    else:
        lines.append("- 최근 뚜렷하게 성장한 상품은 보이지 않습니다.")

    if worst_decline_diff < 0:
        lines.append(f"- 최근 가장 많이 하락한 상품은 {worst_decline_product} ({worst_decline_diff:+,.0f})입니다.")
        lines.append("- 하락 상품은 가격, 노출, 계절성, 대체 상품 등장 여부를 점검해볼 수 있습니다.")
    else:
        lines.append("- 최근 뚜렷하게 하락한 상품은 보이지 않습니다.")

    return lines

def build_highlight_insights(monthly: pd.DataFrame, product: pd.DataFrame, month_product: pd.DataFrame):
    lines = []

    # 최고 / 최저 월
    top_month_row = monthly.sort_values("sales", ascending=False).iloc[0]
    low_month_row = monthly.sort_values("sales", ascending=True).iloc[0]

    top_month = int(top_month_row["month"])
    top_month_sales = float(top_month_row["sales"])

    low_month = int(low_month_row["month"])
    low_month_sales = float(low_month_row["sales"])

    lines.append(f"최고 매출 월: {top_month}월 ({top_month_sales:,.0f})")
    lines.append(f"최저 매출 월: {low_month}월 ({low_month_sales:,.0f})")

    # 상품 성장 / 하락
    trend_rows = []

    for product_name, group in month_product.groupby("product"):
        group = group.sort_values("month").reset_index(drop=True)

        if len(group) >= 2:
            last_sales = float(group.iloc[-1]["sales"])
            prev_sales = float(group.iloc[-2]["sales"])
            diff = last_sales - prev_sales

            trend_rows.append({
                "product": product_name,
                "diff": diff
            })

    if trend_rows:
        trend_df = pd.DataFrame(trend_rows)

        best_growth_row = trend_df.sort_values("diff", ascending=False).iloc[0]
        worst_decline_row = trend_df.sort_values("diff", ascending=True).iloc[0]

        best_growth_product = str(best_growth_row["product"])
        best_growth_diff = float(best_growth_row["diff"])

        worst_decline_product = str(worst_decline_row["product"])
        worst_decline_diff = float(worst_decline_row["diff"])

        if best_growth_diff > 0:
            lines.append(f"성장 상품: {best_growth_product} ({best_growth_diff:+,.0f})")
        else:
            lines.append("성장 상품: 뚜렷한 상승 없음")

        if worst_decline_diff < 0:
            lines.append(f"하락 상품: {worst_decline_product} ({worst_decline_diff:+,.0f})")
        else:
            lines.append("하락 상품: 뚜렷한 하락 없음")
    else:
        lines.append("성장/하락 상품: 분석할 2개월 이상 데이터 부족")

    return lines

def normalize_column_name(col_name: str) -> str:
    return str(col_name).strip().lower().replace(" ", "").replace("_", "")


def guess_column_mapping(columns: list[str]) -> dict:
    month_candidates = ["month", "월", "monthnum", "monthnumber"]
    date_candidates = ["date", "날짜", "판매일", "주문일", "orderdate", "datetime", "일자"]
    product_candidates = ["product", "상품", "상품명", "menu", "메뉴", "메뉴명", "item", "품목"]
    sales_candidates = ["sales", "매출", "매출액", "amount", "revenue", "price", "금액"]

    normalized_map = {col: normalize_column_name(col) for col in columns}

    guessed = {
        "month_col": None,
        "date_col": None,
        "product_col": None,
        "sales_col": None,
    }

    for original, normalized in normalized_map.items():
        if guessed["month_col"] is None and normalized in [normalize_column_name(x) for x in month_candidates]:
            guessed["month_col"] = original

        if guessed["date_col"] is None and normalized in [normalize_column_name(x) for x in date_candidates]:
            guessed["date_col"] = original

        if guessed["product_col"] is None and normalized in [normalize_column_name(x) for x in product_candidates]:
            guessed["product_col"] = original

        if guessed["sales_col"] is None and normalized in [normalize_column_name(x) for x in sales_candidates]:
            guessed["sales_col"] = original

    return guessed