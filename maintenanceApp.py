from flask import Flask, request, render_template, jsonify
from logging import getLogger, DEBUG, INFO, ERROR, WARNING, Formatter, StreamHandler, FileHandler
import sqlite3
import os
import configparser
from contextlib import closing
import json

app = Flask(__name__)
logger = None

@app.route("/")
def index():
    try:
        # アプリカテゴリの取得
        app_sql = create_app_sql()
        print(f"app_sql: {app_sql}")
        apps_data = execution_sql(app_sql)
        
        # ニュース情報の取得
        news_sql = create_news_sql()
        print(f"news_sql: {news_sql}")
        news_data = execution_sql(news_sql)
        
        return render_template('index.html', news_data=news_data, apps_data=apps_data, filter_apps="")
    except Exception as e:
        print(f"(index): {e}")

@app.route("/register", methods=["POST"])
def register_news():
    try:
        news_data = []
        files = []
        for key, value in request.form.items():
            if key.startswith("news_"):
                news_data.append(json.loads(value))
            if key.startswith("file_"):
                files.append(request.files[key])
        
        with closing(sqlite3.connect(app.config['DATABASE_NAME'])) as conn:
            cursor = conn.cursor()
            for news in news_data:
                if news['newRow']:
                    insert_sql, params = create_insert_sql(news)
                    cursor.execute(insert_sql, params)
                    news_id = cursor.lastrowid
                    app_id_sql = "SELECT ID FROM App_Mgmt WHERE AppCategory = ?"
                    cursor.execute(app_id_sql, (news['current'][0],))
                    app_id = cursor.fetchone()[0]
                    id_mgmt_sql = "INSERT INTO ID_Mgmt (NewsID, AppID) VALUES (?, ?)"
                    cursor.execute(id_mgmt_sql, (news_id, app_id))
                else:
                    update_sql, params = create_update_sql(news)
                    cursor.execute(update_sql, params)
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"(register_news): {e}")
        return jsonify({"status": "error", "message": str(e)})

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

def create_news_sql(filter_app_list = []):
    try:
        sql = """
        SELECT App_Mgmt.AppCategory, News_Mgmt.Category, News_Mgmt.Title, News_Mgmt.Year, 
        News_Mgmt.PublicationDate, News_Mgmt.Deadline, News_Mgmt.News_FileName, News_Mgmt.EndFlag 
        FROM News_Mgmt 
        JOIN ID_Mgmt 
        ON News_Mgmt.ID = ID_Mgmt.NewsID 
        JOIN App_Mgmt 
        ON ID_Mgmt.AppID = App_Mgmt.ID 
        """
        where = "WHERE True"
        if len(filter_app_list) > 0:
            where += " AND AppCategory IN (" + ",".join(["?"] * len(filter_app_list)) + ")"
        
        sql = sql + where + ";"
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
        params = (news['current'][1], news['current'][2], news['current'][3], news['current'][4], news['current'][5], news['current'][7], news['current'][6])
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
        params = (news['current'][1], news['current'][2], news['current'][3], news['current'][4], news['current'][5], news['current'][7], news['current'][6], news['original'][0])
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
        # logger = _setup_logger()
    except Exception as e:
        print(f"(read_ini): {e}")

if __name__ == "__main__":
    read_ini()
    app.run(debug=True)
