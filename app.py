import os
import json
import googlemaps
import datetime
import configparser
import spht

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, QuickReplyButton, MessageAction, QuickReply, TextSendMessage, LocationAction, PostbackAction, LocationMessage,LocationSendMessage,)
from linebot.models.actions import DatetimePickerAction
from _ast import And

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

body = ""

# 設定ファイルのパス
CONF_FILEPATH = 'api.conf'
config = configparser.ConfigParser()
config.read(CONF_FILEPATH, 'UTF-8')
# confファイルで[]で囲った場所を指定
config_api = config['API']

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    dict = json.loads(body)
    id = dict["events"][0]["source"]["userId"]

    # postbackで時間が送られてきた場合
    time = ""
    r = allkeys(dict["events"][0])
    print(r)
    for key in r:
        if key == "postback.params.datetime":

            # DB情報取得
            users = spht.input_t_user()
            target_user = {}
            for user_info in users:
                # DB内のIDになかった場合、初回のステータスでDB登録 todo
                if user_info['user_id'] == id:
                    target_user = user_info
                    break

            time = dict["events"][0]["postback"]["params"]["datetime"].replace("T", " ").replace("-", "/")

            target_user['status'] = 2
            target_user['time'] = time
            spht.register_t_user(target_user, 0)

            location_list = ["はい", "いいえ"]
            items = [QuickReplyButton(action=MessageAction(label=f"{loc}", text=f"{loc}を選択しました")) for loc in location_list]
            messages = TextSendMessage(text='時間を'+time+'で登録しました。\r\n出発位置を選択して下さい。',
                                   quick_reply=QuickReply(items=items))
            line_bot_api.reply_message(dict["events"][0]["replyToken"], messages=messages)

        elif key == "message.address":
            # DB情報取得
            users = spht.input_t_user()
            target_user = {}
            for user_info in users:
                # DB内のIDになかった場合、初回のステータスでDB登録 todo
                if user_info['user_id'] == id:
                    target_user = user_info
                    break
            if target_user['status'] == '2':
                lat_from = dict["events"][0]["message"]["latitude"]
                lon_from = dict["events"][0]["message"]["longitude"]

                target_user['status'] = 3
                target_user['lat_from'] = lat_from
                target_user['lon_from'] = lon_from
                spht.register_t_user(target_user, 0)

                location_list = ["はい", "いいえ"]
                items = [QuickReplyButton(action=MessageAction(label=f"{loc}", text=f"{loc}を選択しました")) for loc in location_list]
                messages = TextSendMessage(text='出発位置を登録しました。\r\n到着位置を選択して下さい。',
                                       quick_reply=QuickReply(items=items))
                line_bot_api.reply_message(dict["events"][0]["replyToken"], messages=messages)
            if target_user['status'] == '3':
                lat_to = dict["events"][0]["message"]["latitude"]
                lon_to = dict["events"][0]["message"]["longitude"]

                target_user['status'] = 4
                target_user['lat_to'] = lat_to
                target_user['lon_to'] = lon_to
                spht.register_t_user(target_user, 0)

                # googlemap API todo
                gmaps = googlemaps.Client(key=config_api['GMAP_KEY'])
                duration_result = gmaps.distance_matrix(origins=(target_user['lat_from'], target_user['lon_from']),
                                            destinations=(target_user['lat_to'], target_user['lon_to']), mode='driving')
                print(str(duration_result))
                distance = duration_result['rows'][0]['elements'][0]['distance']['value']
                distance = distance / 1000

                # 参考金額計算
                cost = distance * (140/12)

                location_list = ["完了"]
                items = [QuickReplyButton(action=MessageAction(label=f"{loc}", text=f"{loc}を選択しました")) for loc in location_list]
                messages = TextSendMessage(text='到着位置を登録しました。\r\n完了ボタンを押下しドライバーが確定するまでお待ちください\r\n\r\n距離：' +
                                            str(distance) + ' km\r\n参考金額：'+ str(round(cost)) +' 円です(支払いは不要です)',
                                            quick_reply=QuickReply(items=items))
                line_bot_api.reply_message(dict["events"][0]["replyToken"], messages=messages)


    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def response_message(event):
    # ラインユーザ情報取得
    id = event.source.user_id
    # ユーザー名
    profile = line_bot_api.get_profile(id)
    display_name = profile.display_name

    # DB情報取得
    dicts = spht.input_t_user()
    break_flg = 1
    target_user = {}
    for user_info in dicts:
        # DB内のIDになかった場合、初回のステータスでDB登録 todo
        if user_info['user_id'] == id:
            break_flg = 0
            target_user = user_info
            break

    #テスト用
    if event.message.text == '取消':
        dict_user = {}
        if target_user['type'] == '0':
            dict_user = {'user_id' : target_user['user_id'],
                    'type' : target_user['type'],
                    'status' : 1,
                    'time' : '',
                    'lat_from' : '',
                    'lon_from' : '',
                    'lat_to' : '',
                    'lon_to' : '',
                    'lines' : target_user['lines'],
                    'res_user_id' : '',
                    'display_name' : target_user['display_name'],
                    'tmp_time' : ''}
        elif target_user['type'] == '1' or target_user['type'] == '2':
            dict_user = {'user_id' : target_user['user_id'],
                    'type' : target_user['type'],
                    'status' : 11,
                    'time' : '',
                    'lat_from' : '',
                    'lon_from' : '',
                    'lat_to' : '',
                    'lon_to' : '',
                    'lines' : target_user['lines'],
                    'res_user_id' : '',
                    'display_name' : target_user['display_name'],
                    'tmp_time' : ''}
        target_user = dict_user
    elif event.message.text == '#clear' and break_flg == 0:
        if target_user['status'] == '1' or target_user['status'] == '2' or target_user['status'] == '3' or target_user['status'] == '4' or target_user['status'] == '11':
            dict_user = {}
            if target_user['type'] == '0':
                dict_user = {'user_id' : target_user['user_id'],
                        'type' : target_user['type'],
                        'status' : 1,
                        'time' : '',
                        'lat_from' : '',
                        'lon_from' : '',
                        'lat_to' : '',
                        'lon_to' : '',
                        'lines' : target_user['lines'],
                        'res_user_id' : '',
                        'display_name' : target_user['display_name'],
                        'tmp_time' : ''}
            elif target_user['type'] == '1' or target_user['type'] == '2':
                dict_user = {'user_id' : target_user['user_id'],
                        'type' : target_user['type'],
                        'status' : 11,
                        'time' : '',
                        'lat_from' : '',
                        'lon_from' : '',
                        'lat_to' : '',
                        'lon_to' : '',
                        'lines' : target_user['lines'],
                        'res_user_id' : '',
                        'display_name' : target_user['display_name'],
                        'tmp_time' : ''}
            target_user = dict_user
    elif event.message.text == 'ステータス変更' and break_flg == 0:
        if target_user['status'] == '1' or target_user['status'] == '11':
            type_list = ["利用者", "運転手", "利用者・運転手"]
            items = [QuickReplyButton(action=MessageAction(label=f"{select_type}", text=f"{select_type}を選択しました")) for select_type in type_list]
            messages = TextSendMessage(text="ご利用目的を選択してください\r\n※あとで変更も可能です。変更する際は、「ステータス変更」と入力してください。",
                                   quick_reply=QuickReply(items=items))
            line_bot_api.reply_message(event.reply_token, messages=messages)
        else:
            message = TextSendMessage('ステータス変更ができません。\r\n一度、#clear と話しかけて、状態を戻してから再度変更してください。')
            line_bot_api.reply_message(event.reply_token, message)

    if break_flg == 1:
        type_list = ["利用者", "運転手", "利用者・運転手"]
        items = [QuickReplyButton(action=MessageAction(label=f"{select_type}", text=f"{select_type}を選択しました")) for select_type in type_list]
        messages = TextSendMessage(text="ご利用目的を選択してください\r\n※あとで変更も可能です。変更する際は、「ステータス変更」と入力してください。",
                               quick_reply=QuickReply(items=items))

        dict = {}
        dict = {'user_id' : id,
                'type' : '',
                'status' : 0,
                'time' : '',
                'lat_from' : '',
                'lon_from' : '',
                'lat_to' : '',
                'lon_to' : '',
                'lines' : '',
                'res_user_id' : '',
                'display_name' : display_name,
                'tmp_time' : ''}
        spht.register_t_user(dict, 1)
        line_bot_api.reply_message(event.reply_token, messages=messages)

    elif event.message.text == '利用者を選択しました':
        target_user['type'] = 0
        target_user['status'] = 1
        use_list = ["はい", "いいえ"]
        items = [QuickReplyButton(action=MessageAction(label=f"{use}", text=f"{use}を選択しました")) for use in use_list]
        messages = TextSendMessage(text="このまま利用しますか？",
                               quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, messages=messages)
    elif event.message.text == '運転手を選択しました':
        target_user['type'] = 1
        target_user['status'] = 11
        message = TextSendMessage('配車通知が来るまで、お待ちください。')
        line_bot_api.reply_message(event.reply_token, message)

    elif event.message.text == '利用者・運転手を選択しました':
        target_user['type'] = 2
        target_user['status'] = 11
        use_list = ["はい", "いいえ"]
        items = [QuickReplyButton(action=MessageAction(label=f"{use}", text=f"{use}を選択しました")) for use in use_list]
        message = TextSendMessage(text="このまま利用しますか？",
                               quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, message)

    elif event.message.text == 'いいえを選択しました' and (target_user['type'] == '0' or target_user['type'] == '2') and (target_user['status'] == '1' or target_user['status'] == '11'):
        message = TextSendMessage('次回から利用する場合は 「配車」と入力して呼び出してください')
        line_bot_api.reply_message(event.reply_token, message)

    elif (target_user['status'] == '1' or target_user['status'] == '11') and (target_user['type'] == '0' or target_user['type'] == '2') and event.message.text == '配車':
        items = [QuickReplyButton(action=DatetimePickerAction(label="Select date", data="storeId=12345", mode="datetime", initial="2017-12-25t00:00", max="2018-01-24t23:59", min="2017-12-25t00:00"))]
        messages = [TextSendMessage('利用者(乗車)プロセスを開始します'),
                            TextSendMessage(text="出発時間を設定してください",
                            quick_reply=QuickReply(items=items))]

        line_bot_api.reply_message(event.reply_token, messages=messages)

    elif target_user['status'] == '2':
        items = [QuickReplyButton(action=LocationAction(label="Location_from"))]

        messages = TextSendMessage(text="出発位置を設定してください",
                                   quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, messages=messages)

    elif target_user['status'] == '3':
        items = [QuickReplyButton(action=LocationAction(label="Location_to"))]

        messages = TextSendMessage(text="到着位置を設定してください",
                                   quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, messages=messages)

    elif target_user['status'] == '4':
        target_user['status'] = 5

    elif target_user['status'] == '11':
        if event.message.text == 'いいえを選択しました':
            target_user['status'] = 11
        elif event.message.text == 'はいを選択しました':
            user_list = []
            for user_info in dicts:
                if user_info['type'] == '0' or user_info['type'] == '2' :
                    user_list.append(user_info)

            nobodyFlg = True
            for user in user_list:
                if user['status'] == '5':
                    user['status'] = 6
                    user['res_user_id'] = target_user['user_id']
                    spht.register_t_user(user, break_flg)
                    gmaps = googlemaps.Client(key='AIzaSyCpgc1jvQTokvVo8bjHEZQEkog0EXzXM2Q')

                    ret_json = gmaps.reverse_geocode((user['lat_from'], user['lon_from']))
                    address_from = ''
                    for result in ret_json:
                        address_from = result['formatted_address']
                        break;

                    ret_json = gmaps.reverse_geocode((user['lat_to'], user['lon_to']))
                    address_to = ''
                    for result in ret_json:
                        address_to = result['formatted_address']
                        break;

                    use_list = ["はい", "いいえ"]
                    items = [QuickReplyButton(action=MessageAction(label=f"{use}", text=f"{use}を選択しました")) for use in use_list]
                    messages = [TextSendMessage('予約時間は、'+user['time']+'です。'),
                                    LocationSendMessage(type="location", title="出発地", address=address_from,
                                                latitude=user['lat_from'], longitude=user['lon_from']),
                                    LocationSendMessage(type="location", title="目的地", address=address_to,
                                                latitude=user['lat_to'], longitude=user['lon_to']),
                                    TextSendMessage(text="このまま出発登録しますか？",
                                                                quick_reply=QuickReply(items=items))]
                    line_bot_api.reply_message(event.reply_token, messages=messages)

                    spht.register_t_user(user, break_flg)
                    target_user['status'] = 13
                    target_user['res_user_id'] = user['user_id']
                    target_user['tmp_time'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    nobodyFlg = False
                    break

            if nobodyFlg:
                message = TextSendMessage('すでに他のドライバーが登録済みの為、登録はキャンセルされました。')
                line_bot_api.reply_message(event.reply_token, messages=message)
                target_user['status'] = 11

    elif event.message.text == 'いいえを選択しました' and target_user['status'] == '13':
        message = TextSendMessage('登録を中止しました。')
        line_bot_api.reply_message(event.reply_token, message)
        for user_info in dicts:
            if user_info['user_id'] == target_user['res_user_id']:
                user_info['status'] = 5
                user_info['res_user_id'] = ''
                spht.register_t_user(user_info, break_flg)
                break
        target_user['status'] = 11
        target_user['tmp_time'] = ''

    elif target_user['status'] == '13':
        display_name = ''
        time = ''
        target_user['status'] = 14
        for user_info in dicts:
            if user_info['user_id'] == target_user['res_user_id']:
                display_name = user_info['display_name']
                time = user_info['time']
                user_info['status'] = 7
                spht.register_t_user(user_info, break_flg)
        messages = [TextSendMessage('登録が完了しました。'),
                        TextSendMessage('ご利用ユーザー名：'+ display_name +'\r\n'+'時間:' + time)]
        line_bot_api.reply_message(event.reply_token, messages)

    if break_flg == 0:
        spht.register_t_user(target_user, break_flg)

def allkeys(list_json):
    keys = list(list_json.keys())
    for parent, children in list_json.items():
        if isinstance(children, dict):
            keys.extend(parent + "." + child for child in allkeys(children))
    return keys

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
