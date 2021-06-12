import os

REAL_PATH = os.path.dirname(os.path.realpath(__file__))
FFMPEG = os.path.join(REAL_PATH, "ffmpeg.exe")
TRANSFORM = "{0} -y -i {1} -c copy {2}"

def flv2mp4(flv, mp4):
    command = TRANSFORM.format(FFMPEG, "\""+flv+"\"", "\""+mp4+"\"")
    print(command)
    os.system(command)

if __name__ == "__main__":
    try:
        if not os.path.exists(FFMPEG):
            raise Exception("ffmpeg.exe未找到，请检查本程序所在目录下是否有ffmpeg.exe")
        flv = input("请输入要转换封装的flv文件路径（可直接拖入本窗口）:")
        flv = flv.replace("'", "")
        flv = flv.replace("\"", "")
        print(flv)
        mp4 = flv.split(".")[0] + ".mp4"
        flv2mp4(flv, mp4)
        os.system("pause")
    except Exception as e:
        print(str(e))

