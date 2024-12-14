from flask import Flask, g, render_template, request
import sqlite3

app = Flask(__name__)
DATEBASE = 'Final_Incheon_hospital.db'

def get_db():
    db = getattr(g, 'database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATEBASE)
        db.execute("PRAGMA journal_mode=DELETE")  # WAL 모드 방지
        db.isolation_level = None  # 자동 커밋 설정
    return db


@app.route('/')
def home():
    return render_template('page_1.html')

@app.route('/modify')
def modify():
    return render_template('page_3.html')

@app.route('/modify/add')
def add(): 
    return render_template('page_add.html')

@app.route('/modify/edit')
def edit():
    return render_template('page_edit.html')

@app.route('/modify/delete')
def delete():
    return render_template('page_delete.html')

@app.route('/search_result', methods=['GET'])
def search_result():
    district = request.args.get('district')  # GET 요청은 request.args 사용
    hospital_type = request.args.get('hospitalType')
    specialty = request.args.get('specialty')
    hospital_name = request.args.get('hospitalName')    

    query = """
        SELECT H.병원ID, R.군구명, H.의료기관명, H.병원종별, P.진료과목, D.병상수, D.소재지
        FROM hospital_table H
        JOIN detail_table D ON H.병원ID = D.병원ID
        JOIN region_table R ON H.군구코드 = R.군구명코드
        JOIN part_table P ON H.진료코드 = P.진료과목코드
    """
    params = []

    if district and district != "해당없음":
        query += " AND R.군구명 = ?"
        params.append(district)
    if hospital_type and hospital_type != "해당없음":
        query += " AND H.병원종별 = ?"
        params.append(hospital_type)
    if specialty and specialty != "해당없음":
        query += " AND P.진료과목 = ?"
        params.append(specialty)
    if hospital_name:
        query += " AND H.의료기관명 LIKE ?"
        params.append(f"%{hospital_name}%")

    cur = get_db().cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    return render_template('page_2.html', rows=rows)

@app.route('/check_hospital', methods=['POST'])
def check_hospital():
    hospital_id = request.json.get('hospitalId')
    query = "SELECT 1 FROM hospital_table WHERE 병원ID = ?"
    cur = get_db().cursor()
    cur.execute(query, (hospital_id,))
    result = cur.fetchone()
    return {"exists": bool(result)}

@app.route('/update_hospital', methods=['POST'])
def update_hospital():
    data = request.json
    hospital_id = data.get('hospitalId')  # 병원 ID
    attribute = data.get('attribute')    # 수정할 항목
    new_value = data.get('newValue')     # 새로운 값

    column_map = {
        "region-code": "군구코드",
        "hospital-name": "의료기관명",
        "hospital-type": "병원종별"
    }
    column_name = column_map.get(attribute)

    if not column_name:
        return {"success": False, "message": "잘못된 필드 선택"}

    try:
        query = f"UPDATE hospital_table SET {column_name} = ? WHERE 병원ID = ?"
        print(f"Executing Query: {query} with values: {new_value}, {hospital_id}")
        cur = get_db().cursor()
        cur.execute(query, (new_value, hospital_id))
        get_db().commit()  # 변경사항 저장
        print("Changes committed successfully.")

        # 업데이트된 데이터 확인
        cur.execute("SELECT * FROM hospital_table WHERE 병원ID = ?", (hospital_id,))
        updated_records = cur.fetchall()
        print(f"Updated Records: {updated_records}")

        return {
            "success": True,
            "message": f"{column_name}가 {new_value}(으)로 수정되었습니다.",
            "updatedRecords": updated_records
        }

        
    except sqlite3.Error as e:
        return {"success": False, "message": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=5000)