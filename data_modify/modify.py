import pandas as pd

# CSV 파일 로드 (파일 경로는 필요에 따라 수정)
file_path = '인천광역시_의료기관 현황_20240331.csv'
data = pd.read_csv(file_path, encoding='cp949')

# '진료과목' 열을 분리하여 행으로 확장
data_exploded = data.assign(진료과목=data['진료과목'].str.split('[, ]')).explode('진료과목')

# 공백 제거 및 NaN 값 필터링
data_exploded['진료과목'] = data_exploded['진료과목'].str.strip()
data_exploded = data_exploded[data_exploded['진료과목'].notna() & (data_exploded['진료과목'] != "")]

# 결과 저장
output_path = '인천광역시_의료기관_변환된_진료과목.csv'
data_exploded.to_csv(output_path, index=False, encoding='cp949')

print(f"변환된 데이터가 {output_path}에 저장되었습니다.")
