from flask import Flask, g, render_template, request
import sqlite3

app = Flask(__name__)
DATEBASE = 'Final_Incheon_hospital.db'

def get_db():
    db = getattr(g, 'database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATEBASE)
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
        SELECT H.병원ID, R.군구명, H.병원종별, H.의료기관명, D.소재지, D.병상수, P.진료과목
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

    if result:
        return {"exists": True}
    else:
        return {"exists": False}

    
if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=5000)