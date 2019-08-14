import os
import datetime
import spht
from linebot import LineBotApi
from linebot.models import (
    QuickReplyButton, MessageAction, QuickReply, TextSendMessage)

# リモートリポジトリに"ご自身のチャネルのアクセストークン"をpushするのは、避けてください。
# 理由は、そのアクセストークンがあれば、あなたになりすまして、プッシュ通知を遅れてしまうからです。
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def main():
    print('call push py')
    # DB情報取得
    users = spht.input_t_user()
    user_list = []
    # ドライバー通知
    for user_info in users:
        if user_info['type'] == '1' or user_info['type'] == '2':
            user_list.append(user_info)

    target_user_list = []
    for target_user in user_list:
        if target_user['status'] == '11':
            print('call 11')
            target_user_list.append(target_user)
    for user in target_user_list:
        # 利用登録してあるユーザーがいれば、ドライバー登録通知
        for regist_user in users:
            if regist_user['status'] == '5':
                print('call 5')
                if user['res_user_id'] != regist_user['user_id']:
                    user['res_user_id'] = regist_user['user_id']
                    spht.register_t_user(user, '0')
                    user_id = user['user_id']
                    use_list = ["はい"]
                    items = [QuickReplyButton(action=MessageAction(label=f"{use}", text=f"{use}を選択しました")) for use in use_list]
                    messages = TextSendMessage(text=f"ドライバー通知\n\n"
                                                    f"配車希望があります。配車情報を見ますか？",
                                           quick_reply=QuickReply(items=items))
                    line_bot_api.push_message(user_id, messages=messages)
                else:
                    diff_time = spht.diff_time(regist_user['time'])
                    print('time:'+str(diff_time.total_seconds()))
                    if diff_time.total_seconds() > 0:
                        user['res_user_id'] = ''
                        spht.register_t_user(user, '0')
    # マッチングロック解除
    target_user_list = []
    for target_user in users:
        if target_user['status'] == '13':
            target_user_list.append(target_user)
    for user in target_user_list:
        diff_time = spht.diff_time(user['tmp_time'])
        res_user_id = user['res_user_id']
        if diff_time.total_seconds() > 60:
            for user_info in users:
                if user_info['user_id'] == res_user_id:
                    user_info['status'] = 5
                    user_info['res_user_id'] = ''
                    spht.register_t_user(user_info, '0')
            spht.register_t_user(user_info, '0')
            user['status'] = 11
            user['res_user_id'] = ''
            user['tmp_time'] = ''
            spht.register_t_user(user, '0')
            message = TextSendMessage('ユーザー情報表示から60秒が経過したため、配車ステータスをクリアしました。')
            line_bot_api.push_message(user['user_id'], messages=message)

    # 配車完了通知
    target_user_list = []
    for target_user in users:
        if target_user['status'] == '7':
            target_user_list.append(target_user)
    for user in target_user_list:
        user['status'] = 8
        spht.register_t_user(user, '0')
        user_id = user['user_id']
        for driver in users:
            if user['res_user_id'] == driver['user_id']:
                driver['tmp_time'] = ''
                spht.register_t_user(driver, '0')
                messages = [TextSendMessage('配車手配が完了しました\r\n指定時間にご利用ください'),
                                TextSendMessage('ドライバー名：'+ driver['display_name'] +'\r\n'+'時間:' +user['time'])]
                break
        line_bot_api.push_message(user_id, messages=messages)

    # リマインダー
    target_user_list = []
    for target_user in users:
        if target_user['status'] == '8' or target_user['status'] == '5':
            target_user_list.append(target_user)
    for user in target_user_list:
        on_date = datetime.datetime.now()
        user_date = datetime.datetime(year=int(user['time'][0:4]), month=int(user['time'][5:7]),
                                            day=int(user['time'][8:10]), hour=int(user['time'][11:13]), minute=int(user['time'][14:16]))
        diff_time = user_date - on_date
        print('remind:'+str(diff_time.total_seconds()))
        if diff_time.total_seconds() < 1800:
            if user['status'] == '5':
                for driver in users:
                    if user['user_id'] == driver['res_user_id']:
                        driver['res_user_id'] = ''
                        spht.register_t_user(driver, '0')
                dict_user = {}
                if user['type'] == '0':
                    dict_user = {'user_id' : user['user_id'],
                            'type' : user['type'],
                            'status' : 1,
                            'time' : '',
                            'lat_from' : '',
                            'lon_from' : '',
                            'lat_to' : '',
                            'lon_to' : '',
                            'lines' : user['lines'],
                            'res_user_id' : '',
                            'display_name' : user['display_name'],
                            'tmp_time' : ''}
                elif user['type'] == '2':
                    dict_user = {'user_id' : user['user_id'],
                            'type' : user['type'],
                            'status' : 11,
                            'time' : '',
                            'lat_from' : '',
                            'lon_from' : '',
                            'lat_to' : '',
                            'lon_to' : '',
                            'lines' : user['lines'],
                            'res_user_id' : '',
                            'display_name' : user['display_name'],
                            'tmp_time' : ''}
                spht.register_t_user(dict_user, '0')
                message = TextSendMessage('運転手が見つからなかったため、利用登録はキャンセルされました。')
                line_bot_api.push_message(user['user_id'], messages=message)
                break
            else:
                user['status'] = 9
                spht.register_t_user(user, '0')
                users_id = [user['user_id'], user['res_user_id']]
                for user_id in users_id:
                    message = TextSendMessage('利用時間30分前です\r\n' + user['time'] + 'にご利用予定')
                    line_bot_api.push_message(user_id, messages=message)

    # 完了通知
    target_user_list = []
    for target_user in users:
        if target_user['status'] == '9':
            target_user_list.append(target_user)
    for user in target_user_list:
        on_date = datetime.datetime.now()
        user_date = datetime.datetime(year=int(user['time'][0:4]), month=int(user['time'][5:7]),
                                            day=int(user['time'][8:10]), hour=int(user['time'][11:13]), minute=int(user['time'][14:16]))
        diff_time = on_date - user_date
        if diff_time.total_seconds() > 900:
            users_id = [user['user_id'], user['res_user_id']]
            user['status'] = 10
            spht.register_t_user(user, '0')
            for user_id in users_id:
                message = TextSendMessage('ご利用有難うございました。\r\nまたのご利用をお待ちしております。')
                line_bot_api.push_message(user_id, messages=message)

            #利用者側初期化
            dict_user = {}
            if user['type'] == '0':
                dict_user = {'user_id' : user['user_id'],
                        'type' : user['type'],
                        'status' : 1,
                        'time' : '',
                        'lat_from' : '',
                        'lon_from' : '',
                        'lat_to' : '',
                        'lon_to' : '',
                        'lines' : user['lines'],
                        'res_user_id' : '',
                        'display_name' : user['display_name'],
                        'tmp_time' : ''}
            elif user['type'] == '2':
                dict_user = {'user_id' : user['user_id'],
                        'type' : user['type'],
                        'status' : 11,
                        'time' : '',
                        'lat_from' : '',
                        'lon_from' : '',
                        'lat_to' : '',
                        'lon_to' : '',
                        'lines' : user['lines'],
                        'res_user_id' : '',
                        'display_name' : user['display_name'],
                        'tmp_time' : ''}
            spht.register_t_user(dict_user, '0')

            for driver in users:
                if driver['user_id'] == user['res_user_id']:
                    # ドライバー側初期化
                    dict_driver = {}
                    dict_driver = {'user_id' : driver['user_id'],
                            'type' : driver['type'],
                            'status' : 11,
                            'time' : '',
                            'lat_from' : '',
                            'lon_from' : '',
                            'lat_to' : '',
                            'lon_to' : '',
                            'lines' : driver['lines'],
                            'res_user_id' : '',
                            'display_name' : driver['display_name'],
                            'tmp_time' : ''}
                    spht.register_t_user(dict_driver, '0')

if __name__ == "__main__":
    main()
