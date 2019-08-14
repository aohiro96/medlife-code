#!/bin/bash

## リトライ処理
RETRY_COUNT=172800    # リトライ回数
RETRY_INTERVAL=30     # リトライ間隔60秒

while [[ $COUNT -ne $RETRY_COUNT ]]
do
    COUNT=`expr $COUNT + 1`
    python push_message_sender.py
    sleep $RETRY_INTERVAL
done
