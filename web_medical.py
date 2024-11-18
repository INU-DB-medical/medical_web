from flask import Flask, g, render_template, request
import sqlite3

app = Flask(__name__)
DATEBASE = 'Incheon_hospital.db'

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

@app.route('/search_result', methods=['POST'])
def search_result():
    district = request.form.get('district')
    hospital_type = request.form.get('hospitalType')
    specialty = request.form.get('specialty')
    hospital_name = request.form.get('hospitalName')    
    
    query = "SELECT * FROM 인천광역시_의료기관_현황 WHERE 1=1"
    params = []
    
    if district != "해당없음":
        query += " AND 군구명 = ?"
        params.append(district)
    if hospital_type != "해당없음":
        query += " AND 병원종별 = ?"
        params.append(hospital_type)
    if specialty != "해당없음":
        query += " AND 진료과목 = ?"
        params.append(specialty)
    if hospital_name:
        query += " AND 의료기관명 LIKE ?"
        params.append(f"%{hospital_name}%")
            
    cur = get_db().cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    
    return render_template('page_2.html', rows=rows)    
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=5000)