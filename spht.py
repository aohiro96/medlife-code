import gspread
import configparser
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# 設定ファイルのパス
CONF_FILEPATH = 'api.conf'

config = configparser.ConfigParser()
config.read(CONF_FILEPATH, 'UTF-8')

# confファイルで[]で囲った場所を指定
config_api = config['API']

def input_t_user():
    #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    #認証情報設定
    #ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
    credentials = ServiceAccountCredentials.from_json_keyfile_name(config_api['JSON_KEY_FILE'], scope)
    #OAuth2の資格情報を使用してGoogle APIにログインします。
    gc = gspread.authorize(credentials)
    #共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
    SPREADSHEET_KEY = config_api['SPREAD_SHEETS_KEY']
    #共有設定したスプレッドシートのt_userシートを開く
    worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(config_api['SHEET_NAME'])

    #全行取得
    values=worksheet.get_all_values()
    last_row = len(values)

    #セルの値を受け取る
    dto = []
    for key in range(1, last_row):
        dict = {}
        dict = {'user_id' : values[key][0],
                'type' : values[key][1],
                'status' : values[key][2],
                'time' : values[key][3],
                'lat_from' : values[key][4],
                'lon_from' : values[key][5],
                'lat_to' : values[key][6],
                'lon_to' : values[key][7],
                'lines' : values[key][8],
                'res_user_id' : values[key][9],
                'display_name' : values[key][10],
                'tmp_time' : values[key][11]}
        dto.append(dict)

    return dto

def register_t_user(user_info, is_first):
    #2つのAPIを記述しないとリフレッシュトークンを3600秒毎に発行し続けなければならない
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

    #認証情報設定
    #ダウンロードしたjsonファイル名をクレデンシャル変数に設定（秘密鍵、Pythonファイルから読み込みしやすい位置に置く）
    credentials = ServiceAccountCredentials.from_json_keyfile_name(config_api['JSON_KEY_FILE'], scope)

    #OAuth2の資格情報を使用してGoogle APIにログインします。
    gc = gspread.authorize(credentials)

    #共有設定したスプレッドシートキーを変数[SPREADSHEET_KEY]に格納する。
    SPREADSHEET_KEY = config_api['SPREAD_SHEETS_KEY']

    #共有設定したスプレッドシートのシート1を開く
    worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet(config_api['SHEET_NAME'])
    if is_first == 1:
        #全行取得
        values=worksheet.get_all_values()
        last_row = len(values)
        user_info['lines'] = last_row + 1

    cell_list = worksheet.range(user_info['lines'], 1, user_info['lines'], 12)
    cell_list[0].value = user_info['user_id']
    cell_list[1].value = user_info['type']
    cell_list[2].value = user_info['status']
    cell_list[3].value = user_info['time']
    cell_list[4].value = user_info['lat_from']
    cell_list[5].value = user_info['lon_from']
    cell_list[6].value = user_info['lat_to']
    cell_list[7].value = user_info['lon_to']
    cell_list[8].value = user_info['lines']
    cell_list[9].value = user_info['res_user_id']
    cell_list[10].value = user_info['display_name']
    cell_list[11].value = user_info['tmp_time']

    worksheet.update_cells(cell_list)

def diff_time(time):
    on_date = datetime.datetime.now()
    user_date = datetime.datetime(year=int(time[0:4]), month=int(time[5:7]),
                                        day=int(time[8:10]), hour=int(time[11:13]), minute=int(time[14:16]))
    diff_time = on_date - user_date

    return diff_time
