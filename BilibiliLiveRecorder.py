from Live import BiliBiliLive, BilibiliLive
import os
import requests
import time
import re
import json
import urllib3
import threading
urllib3.disable_warnings()

from datetime import datetime

REAL_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = REAL_PATH+"/log.log"
RECORD_FILE_PATH = REAL_PATH + "/recordFiles/"
DEFAULT_CHECK_INTERVAL = 60
TIMEOUT = 60*5
VERSION = "1.5.1"
FFMPEG = os.path.join(REAL_PATH, "ffmpeg.exe")
TRANSFORM = "{0} -y -i {1} -c copy {2}"


class BiliBiliLiveRecorder(BiliBiliLive, threading.Thread):
    def __init__(self, room_id, checkInterval=DEFAULT_CHECK_INTERVAL, recordFilePath=RECORD_FILE_PATH, timeout=TIMEOUT):
        BiliBiliLive.__init__(self, room_id)
        threading.Thread.__init__(self)
        self.log = Log # 日志模块
        self.checkInterval = checkInterval # 检测延迟
        self.recordFilePath = recordFilePath # 存放位置
        self.isRecord = False
        self.timeout = timeout
        self.downloadSize = 0
    
    def flv2mp4(flv, mp4):
        command = TRANSFORM.format(FFMPEG, "\""+flv+"\"", "\""+mp4+"\"")
        os.system(command)

    def check(self):
        try:
            roomInfo = self.get_room_info()
            if roomInfo['status']:
                self.roomName = roomInfo["roomname"]
                if not self.isRecord:
                    self.log(self.room_id, self.roomName).success()
                self.isRecord = True
            else:
                self.isRecord = False
                self.log(self.room_id, '等待开播').success()
        except Exception as e:
            self.log(self.room_id, str(e)).error()
        return self.isRecord

    def record(self, recordFilename):
        while self.isRecord:
            try:
                self.downloadSize = 0
                recordUrl = self.get_live_urls()[0]
                self.log(self.room_id, '√ 正在录制...').success()
                headers = {
                    'Accept-Encoding': 'identity',
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
                    'Referer' : re.findall(r'(https://.*\/).*\.flv', recordUrl)[0],
                }
                response = requests.get(recordUrl, stream=True, headers=headers)
                with open(recordFilename, "ab") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk if chunk else None)
                        self.downloadSize += 1024
            except Exception as e:
                self.log(self.room_id, str(e)).error()
            self.check()

    def run(self):
        while True:
            try:
                while not self.check():
                    time.sleep(self.checkInterval)
                streamTime = datetime.now().strftime("%Y-%m-%d %H%M")
                filename_flv = self.recordFilePath+"{0} {1}.flv".format(streamTime, self.roomName)
                filename_mp4 = self.recordFilePath+"{0} {1}.mp4".format(streamTime, self.roomName)
                self.record(filename_flv)
                self.log(self.room_id, '录制完成' + filename_flv).success()
                self.flv2mp4(filename_flv, filename_mp4)
            except Exception as e:
                self.log(self.room_id, str(e)).error()

class Log:
    def __init__(self, roomId, logInfo):
        self.logInfo = logInfo
        self.roomId = roomId
        self.logTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def success(self):
        log = self.logTime+"[INFO]:直播间【{0}】 {1}".format(self.roomId,self.logInfo)
        with open(LOG_PATH, "a", encoding="UTF-8") as f:
            f.write(log+"\n")
        print(log)
    
    def error(self):
        log = self.logTime+"[ERROR]:直播间【{0}】 {1}".format(self.roomId,self.logInfo)
        with open(LOG_PATH, "a", encoding="UTF-8") as f:
            f.write(log+"\n")
        print(log)

class Monitor(threading.Thread):
    def __init__(self, recordThread):
        super().__init__()
        self.recordThread = recordThread

    def run(self):
        while True:
            while not self.recordThread.isRecord:
                time.sleep(3)
            while self.recordThread.isRecord:
                size = self.transform(self.recordThread.downloadSize)
                size_info = "\r"+datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"[INFO]:直播间【{0}】当前已下载==>{1}".format(self.recordThread.room_id, size)
                print("\r"+" "*len(size_info), end="")
                print(size_info, end="")
                time.sleep(1)
            print("")

    def transform(self, size):
        counter = 0
        while size > 1024:
            counter += 1
            size /= 1024
        size = round(size, 2)
        if counter == 0:
            size = str(size)+"bytes"
        elif counter == 1:
            size = str(size)+"KB"
        elif counter == 2:
            size = str(size)+"MB"
        elif counter == 3:
            size = str(size)+"GB"
        elif counter == 4:
            size = str(size)+"TB"
        elif counter == 5:
            size = str(size)+"PB"
        elif counter == 6:
            size = str(size)+"ZB"
        else:
            size = "您太离谱了"
        
        return size

if __name__ == '__main__':
    try:
        if not os.path.exists(RECORD_FILE_PATH) :
            os.mkdir(RECORD_FILE_PATH)
        if not os.path.exists(FFMPEG):
            raise Exception("ffmpeg.exe未找到，请检查本程序所在目录下是否有ffmpeg.exe")
        with open(REAL_PATH+"/config.json") as f:
            data = json.load(f)
        recorder = BiliBiliLiveRecorder(data["room_id"])
        monitor = Monitor(recordThread=recorder)
        print("Bilibili Live Recorder v{}".format(VERSION))
        print("Powered by Python")
        recorder.start()
        monitor.start()
        recorder.join()
        monitor.join()
    except Exception as e:
        print(str(e)+"==>"+str(e.__traceback__.tb_lineno))
    os.system("pause")

