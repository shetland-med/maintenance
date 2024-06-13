from flask import Flask, request, render_template, jsonify
from logging import getLogger, DEBUG, INFO, ERROR, WARNING, Formatter, StreamHandler, FileHandler
import sqlite3
import os
import configparser
from contextlib import closing
import json
from datetime import datetime, timedelta

app = Flask(__name__)
logger = None

@app.route("/")
def index():
    try:
        # アプリカテゴリの取得
        app_sql = create_app_sql()
        apps_data = execution_sql(app_sql)
        
        # ニュース情報の取得
        news_sql = create_news_sql()
        news_data = execution_sql(news_sql)
        print(f"news_data:{news_data}")
        news_data = create_status(news_data)
        
        return render_template('index.html', news_data=news_data, apps_data=apps_data)
    except Exception as e:
        print(f"(index): {e}")

@app.route("/register", methods=["POST"])
def register_news():
    try:
        dic = {}
        for key, value in request.form.items():
            k = str(key.split("_")[1])
            if k not in dic.keys():
                dic[k] = {}
                
            if key.startswith("news"):
                dic[k]["news"] = json.loads(value)
                
        for key in request.files:
            k = str(key.split("_")[1])
            if k not in dic.keys():
                dic[k] = {}        
            
            if key.startswith("file"):
                dic[k]["file"] = request.files[key]
                
                
        
        with closing(sqlite3.connect(app.config['DATABASE_NAME'])) as conn:
            cursor = conn.cursor()
            for val in dic.values():
                news = val['news']
                file = None
                if "file" in val:
                    file = val["file"]
                    
                # ディレクトリが存在しない場合は作成
                if not os.path.exists(app.config['OUTPUT_DIR']):
                    os.makedirs(app.config['OUTPUT_DIR'])
                    
                if file is not None:
                    # 現在の日時を取得
                    now = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    base, extension = os.path.splitext(file.filename)
                    file_name = f"{base}_{now}{extension}"
                    # ファイル名をリネーム
                    news['current']['6'] = file_name
                    
                app_id = select_appID(cursor, news['current']['0'])
                if news['newRow']:
                    insert_sql, params = create_insert_sql(news)
                    cursor.execute(insert_sql, params)
                    news_id = cursor.lastrowid
                    id_mgmt_sql = "INSERT INTO ID_Mgmt (NewsID, AppID) VALUES (?, ?)"
                    cursor.execute(id_mgmt_sql, (news_id, app_id))
                else:
                    update_sql, params = create_update_sql(news)
                    cursor.execute(update_sql, params)
                    id_mgmt_sql = "Update ID_Mgmt SET AppID = ? Where NewsID = ?"
                    cursor.execute(id_mgmt_sql, (app_id, news['current']['8']))
                    
                # ファイルのアップロード
                if file:
                    # ファイル名と日付を結合
                    filename = os.path.join(app.config['OUTPUT_DIR'], file_name)
                    file.save(filename)
                    
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"(register_news): {e}")
        return jsonify({"status": "error", "message": str(e)})
    
def select_appID(cursor, category):
    try:
        app_id_sql = "Select id from App_Mgmt Where AppCategory = ?"
        cursor.execute(app_id_sql, (category,))
        app_id = cursor.fetchone()[0]

        return app_id
    except Exception as e:
        print(f"(select_appID): {e}")
        
# ステータスの追加
def create_status(news_data):
    try:
        data = []
        for row in news_data:
            # 指定した日付
            specified_date_str = row[4]
            specified_date = datetime.strptime(specified_date_str, "%Y-%m-%d")
            
            li = list(row)
            li[4] = specified_date.strftime("%Y-%m-%d")

            # 公開期間の日数を加える
            days_to_add = row[5]
            end_date = specified_date + timedelta(days=days_to_add)

            # 現在の日付を取得
            current_date = datetime.now()

            # 非表示フラグ
            hidden_flg = row[7]

            # 現在日付が公開期間内かどうかを判断
            if specified_date < current_date < end_date and hidden_flg == 0:
                li.append("掲載中")
            elif end_date < current_date or hidden_flg == 1:
                li.append("掲載終了")
            else:
                li.append("")

            data.append(li)

        return data
    except Exception as e:
        print(f"create_status:{e}")


# sql文の実行
def execution_sql(sql, params=[]):
    try:
        with closing(sqlite3.connect(app.config['DATABASE_NAME'])) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        print(f"(execution_sql): {e}")

# アプリカテゴリ用SQL文の作成
def create_app_sql():
    try:
        sql = """
        SELECT AppCategory From App_Mgmt;
        """
        return sql
    except Exception as e:
        print(f"(create_app_sql): {e}")

def create_news_sql():
    try:
        sql = """
        SELECT App_Mgmt.AppCategory, News_Mgmt.Category, News_Mgmt.Title, News_Mgmt.Year, 
        News_Mgmt.PublicationDate, News_Mgmt.Deadline, News_Mgmt.News_FileName, News_Mgmt.EndFlag, News_Mgmt.ID
        FROM News_Mgmt 
        JOIN ID_Mgmt 
        ON News_Mgmt.ID = ID_Mgmt.NewsID 
        JOIN App_Mgmt 
        ON ID_Mgmt.AppID = App_Mgmt.ID; 
        """
        return sql
    except Exception as e:
        print(f"(create_news_sql): {e}")

# ニュース登録用SQL文の作成
def create_insert_sql(news):
    try:
        sql = """
        INSERT INTO News_Mgmt (Category, Title, Year, PublicationDate, Deadline, EndFlag, News_FileName)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (news['current']['1'], news['current']['2'], news['current']['3'], news['current']['4'], news['current']['5'], news['current']['7'], news['current']['6'])
        return sql, params
    except Exception as e:
        print(f"(create_insert_sql): {e}")
        return None, None

# ニュース更新用SQL文の作成
def create_update_sql(news):
    try:
        sql = """
        UPDATE News_Mgmt SET Category = ?, Title = ?, Year = ?, PublicationDate = ?, Deadline = ?, EndFlag = ?, News_FileName = ?
        WHERE ID = ?
        """
        params = (news['current']['1'], news['current']['2'], news['current']['3'], news['current']['4'], news['current']['5'], news['current']['7'], news['current']['6'], news['current']['8'])
        return sql, params
    except Exception as e:
        print(f"(create_update_sql): {e}")
        return None, None

# iniファイルの読み込み
def read_ini():
    try:
        global logger 
        config = configparser.ConfigParser()
        config.read('config.ini')
        app.config['DATABASE_NAME'] = config['DATABASE']['db_path']
        app.config['OUTPUT_DIR'] = config['OUTPUT_DIR']['dir_path']
        # logger = _setup_logger()
    except Exception as e:
        print(f"(read_ini): {e}")

if __name__ == "__main__":
    read_ini()
    app.run(debug=True)
