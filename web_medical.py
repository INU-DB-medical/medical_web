from flask import Flask, g, render_template, request,redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key='your_secret_key'
DATEBASE = 'Final_Incheon_hospital.db'

PASSWORD='1234'

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

@app.route('/password')
def password_page():
    return render_template('password.html')

@app.route('/verify_password', methods=['POST'])
def verify_password():
    entered_password = request.form.get('password')
    if entered_password == PASSWORD:
        session['authenticated'] = True 
        return redirect(url_for('modify')) 
    else:
        return "비밀번호가 틀렸습니다. <a href='/password'>다시 시도하기</a>"


@app.route('/modify')
def modify():
    if not session.get('authenticated'): 
        return redirect(url_for('password_page')) 
    return render_template('page_3.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)  
    return redirect(url_for('home'))

@app.route('/modify/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # 폼 데이터 가져오기
        district = request.form.get('district')
        hospital_type = request.form.get('hospitalType')
        specialty = request.form.get('specialty')
        hospital_id = request.form.get('hospitalId')
        hospital_name = request.form.get('hospitalName')
        num_beds = request.form.get('bed')
        address = request.form.get('address')

        # 데이터베이스에 추가전에 중복 검사
        try:
            db = get_db()
            cursor = db.cursor()
            
             # 군구명 코드를 얻기 위한 쿼리
            cursor.execute("SELECT 군구명코드 FROM region_table WHERE 군구명 = ?", (district,))
            district = cursor.fetchone()
            if district:
                district = district[0]
            else:
                flash("해당 군구명이 존재하지 않습니다.", "success")
            
            # 진료과목 코드를 얻기 위한 쿼리
            cursor.execute("SELECT 진료과목코드 FROM part_table WHERE 진료과목 = ?", (specialty,))
            specialty = cursor.fetchone()
            if specialty:
                specialty = specialty[0]
            else:
                flash("해당 진료과목이 존재하지 않습니다.", "success")
            
            cursor.execute("""
                SELECT 1 FROM hospital_table H
                JOIN part_table P ON H.진료코드 = P.진료과목코드
                WHERE H.병원ID = ? AND P.진료과목 = ?
            """, (hospital_id, specialty))
            existing_record = cursor.fetchone()

            if existing_record:
                return "해당 병원 ID와 진료과목이 이미 존재합니다."

            # 데이터베이스에 추가
            cursor.execute("""
                INSERT INTO hospital_table (병원ID, 군구명코드, 의료기관명, 병원종별, 진료코드)
                VALUES (?, ?, ?, ?, ?)
            """, (hospital_id, district, hospital_name, hospital_type, specialty))

            cursor.execute("""
                INSERT INTO detail_table (병원ID, 병상수, 소재지)
                VALUES (?, ?, ?)
            """, (hospital_id, num_beds, address))

            # DB에 병원 추가 성공
            db.commit()
            flash("병원 정보가 성공적으로 삭제되었습니다.", "success")
            
        except Exception as e:
            db.rollback()
            return f"오류 발생: {str(e)}"
    return render_template('page_add.html')

@app.route('/modify/edit')
def edit():
    return render_template('page_edit.html')

@app.route('/modify/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        hospital_id = request.form.get('hospitalId')
        
        try:
            db = get_db()
            cursor = db.cursor()
            
            # 병원ID가 존재하는지 확인
            cursor.execute("SELECT 1 FROM hospital_table WHERE 병원ID = ?", (hospital_id,))
            existing_record = cursor.fetchone()

            if not existing_record:
                flash("해당 병원 ID는 존재하지 않습니다.", "success")
            
            # 병원 관련 데이터 삭제
            cursor.execute("DELETE FROM detail_table WHERE 병원ID = ?", (hospital_id,))
            cursor.execute("DELETE FROM hospital_table WHERE 병원ID = ?", (hospital_id,))
            
            # DB에 삭제 사항 반영
            db.commit()
            flash("병원 정보가 성공적으로 추가되었습니다.", "success")
        
        except Exception as e:
            db.rollback()
            return f"오류 발생: {str(e)}"
    return render_template('page_delete.html')

@app.route('/search_result', methods=['GET'])
def search_result():
    district = request.args.get('district')  # GET 요청은 request.args 사용
    hospital_type = request.args.get('hospitalType')
    specialty = request.args.get('specialty')
    hospital_name = request.args.get('hospitalName')    

    query = """
        SELECT H.병원ID, R.군구명, H.병원종별, H.의료기관명, D.소재지, D.병상수, GROUP_CONCAT(P.진료과목)
        FROM hospital_table H
        JOIN detail_table D ON H.병원ID = D.병원ID
        JOIN region_table R ON H.군구명코드 = R.군구명코드
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
        
    query += """
        GROUP BY H.병원ID, R.군구명, H.병원종별, H.의료기관명, D.소재지, D.병상수
    """

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
        "region-code": "군구명코드",
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