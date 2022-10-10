"""
==================================================
@Time: 2022/8/11 13:32
@Author: dsj
@File: BaseCapsule.py
@IDE: PyCharm
==================================================
"""
import os
import cv2
import time
import json
import redis
import random
import pickle
import shutil
import logging
import datetime
import threading
import configparser
import numpy as np
import logging.handlers
from queue import Queue
from abc import ABC, ABCMeta
from concurrent.futures import ThreadPoolExecutor


class Data(object):
    """
    使用Data类构建数据结构，该数据结构包含属性
    'puType': PU的类型,
    'puCode': PU的唯一标识符,
    'screenshot': 是否获取第一帧数据,
    'switchCode': 是否停止任务,
    'currentChannel': 当前通道,
    'parentTaskId': 父任务的唯一ID,
    'sourcePaths': 数据来源(视频路径或者rtsp流地址),
    'traceFormworkId': PU的链路,
    'traceId': ,
    """

    def __init__(self, data):
        """
        :param data: json格式的数据(字典格式)
        """
        # self.__dict__ = data
        self.puType = data["puType"]
        self.puCode = data["puCode"]
        self.sourcePaths = data["sourcePaths"]
        self.screenshot = data["screenshot"]
        self.switchCode = data["switchCode"]
        self.currentChannel = data["currentChannel"]
        self.parentTaskId = data["parentTaskId"]
        self.traceFormworkId = data["traceFormworkId"]
        self.traceId = data["traceId"]
        self.taskId = data["taskId"]
        self.timestamp = data["timestamp"]

        self.image = None
        if "frameId" in data.keys():
            self.frameId = data['frameId']
        else:
            self.frameId = None
        if "output" in data.keys():
            if isinstance(data["output"], str):
                data["output"] = json.loads(data["output"])
            self.detection = data["output"]["detection"]
        else:
            self.detection = {
                "classname": "",
                "attributes": {},
                "confidences": [],
                "coords": [],
                "traceId": [],
                "reId": [],
                "feature": []
            }
        self.result = {
            "eventType": "",
            "files": [],
            "startTime": "",
            "endTime": ""
        }

    def update_puType(self, value):
        # 首先使用断言判断value的数据类型是否和puType数据类型相同
        self.puType = value

    def update_puCode(self, value):
        # 首先使用断言判断value的数据类型是否和puType数据类型相同
        self.puCode = value


class Logger(object):
    """
    This is get log class
    """

    def __init__(self, path, name, Flevel=logging.INFO):
        self.time = time.strftime("%Y-%m-%d")
        self.fileName = path + name + "-" + self.time + ".log"
        # 创建一个日志记录器logger,将日志记录到fileName文件中
        self.logger = logging.getLogger(self.fileName)
        # 设置日志的等级
        self.logger.setLevel(Flevel)
        # 定义消息的输出格式
        fmt = logging.Formatter('[%(asctime)s %(threadName)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        # 创建Handler，将日志写入文件
        fh = logging.FileHandler(self.fileName)
        # 设置写入日志文件Handler的日志文件
        fh.setFormatter(fmt)
        fh.setLevel(Flevel)
        # 将Handler添加到日志记录器logger里面
        self.logger.addHandler(fh)

        # 创建一个StreamHandler用于控制输出日志
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        self.logger.addHandler(ch)

        # 设置日志保留时间
        th = logging.handlers.TimedRotatingFileHandler(filename=self.fileName, when='MIDNIGHT',
                                                       interval=1, backupCount=7, encoding='utf-8')
        th.setFormatter(fmt)
        th.setLevel(logging.INFO)
        self.logger.addHandler(th)

    def debug(self, message):
        """
        This is debug
        """
        self.logger.debug(message)

    def info(self, message):
        """
        This is info
        """
        self.logger.info(message)

    def warn(self, message):
        """
        This is warn
        """
        self.logger.warn(message)

    def error(self, message):
        """
        This is error
        """
        self.logger.error(message)

    def critical(self, message):
        """
        This is critical
        """
        self.logger.critical(message)


class BaseCapsule(ABC):
    """
    An abstract base class that all capsules must sub class. Defines the interface that capsule are expexted to implement.
    A class that subclass from this class is expected to dedined in a capsule file in a capsule
    """

    def __init__(self, config):
        """
        :param config:配置文件
        """
        # 读取配置文件
        self.conf = configparser.ConfigParser()
        self.conf.read(config)

        # 获取host和port用来进行数据传输(数据传输的redis和数据存储的redis使用的不是同一个redis)
        self.host = self.conf.get("ICV-runtime-deployment", "IPAddress")
        self.port = self.conf.get("ICV-runtime-deployment", "Port")
        self.password = self.conf.get("ICV-runtime-deployment", "password")

        # 将输入输出转化为列表
        self.input = eval(self.conf.get("puInfo", "inputs"))
        self.output = eval(self.conf.get("puInfo", "outputs"))
        self.puCode = self.conf.get("puInfo", "puCode")
        self.puType = self.conf.get("puInfo", "puType")
        self.testPath = "/data-nfs24/icv/sftp/camera/runtime/"

        self.pool = redis.ConnectionPool(host=self.host, port=self.port, password=self.password)
        self.coon = redis.Redis(connection_pool=self.pool, decode_responses=True)

        self.redis_pool = redis.ConnectionPool(host=self.host, port=6888, password=self.password)
        self.redis_coon = redis.Redis(connection_pool=self.redis_pool, decode_responses=True)

        # 基于输入通道的命名规则定义输入通道(classname只有一个, attribute可能会有多个)
        self.inputChannel = []
        for input in self.input:
            inputchannel_name = "SUB_" + self.puCode + "_"
            if input['classname']:
                inputchannel_name = inputchannel_name + input['classname']
                if input["attaributes"]:
                    for attribute in input["attaributes"]:
                        self.inputChannel.append(inputchannel_name + attribute)
                else:
                    self.inputChannel.append(inputchannel_name)

        # 基于输出通道的命名规则定义输入通道
        self.outputChannel = []
        for output in self.output:
            outputchannel_name = "PUB_" + self.puCode + "_"
            if output['classname']:
                outputchannel_name = outputchannel_name + output['classname']
                if output["attaributes"]:
                    for attribute in output["attaributes"]:
                        self.outputChannel.append(outputchannel_name + attribute)
                else:
                    self.outputChannel.append(outputchannel_name)

        self.resultChannel = "RESULT_" + self.puCode
        self.registerChannel = self.conf.get("puInfo", "RegisterChannel")

        # 首先判断日志文件是否存在，如果存在则先删除日志文件
        if not os.path.exists(self.conf.get("puInfo", "LogPath")):
            os.makedirs(self.conf.get("puInfo", "LogPath"))
        # 首先判断日志文件夹是否存在，如果日志文件夹
        self.logPath = self.conf.get("puInfo", "LogPath")
        if not os.path.exists(self.logPath):
            os.makedirs(self.logPath)
        # 实例化日志对象
        self.logger = Logger(path=self.logPath, name=self.puCode, Flevel=logging.INFO)
        self.resultPath = self.conf.get("puInfo", "ResultPath")
        if not os.path.exists(self.resultPath):
            os.makedirs(self.resultPath)

        # 构建数据同步中心
        self.data_sync = {}

        # 构建数据中心用来缓存数据，并将数据输出到输出队列
        self.data_center = {}

        # 停止任务的数据缓存中心
        self.stop_data = {}
        # 初始化订阅数据队列, 该队列里存放的数据是经过第三方开发者需要的经过处理的数据
        self.sub_queue = Queue(64)
        # 初始化发布数据的队列，该队列存放的数据是经过模型或者业务逻辑推理得到的队列
        self.pub_queue = Queue(64)

        self.param_queue = Queue(8)
        self.paramStatus = True

    def _publish(self, message, channel):
        """
        发布数据
        :param message: 发布数据的信息
        :param channel: 发布数据的通道
        :return:
        """
        self.coon.publish(channel, message)

    def _subscribe(self, channel):
        """
        订阅数据
        :param channel: 订阅数据的通道(订阅数据的通道是一个列表  )
        :return: 返回订阅到的数据
        """
        pub = self.coon.pubsub()
        pub.subscribe(channel)
        pub.parse_response()
        return pub

    def _unsubscribe(self, channel):
        """
        取消订阅
        :param channel:取消订阅的通道数
        :return:
        """
        self.coon.pubsub().unsubscribe(channel)

    def _insert(self, data, deadtime=10):
        """
        从队列中获取数据，并将数据存储到redis数据库中
        """
        for key, value in data.items():
            # 压缩并存储数据
            b = pickle.dumps(value)
            self.redis_coon.set(key, b, deadtime)

    def _get(self, frameId):
        """
        基于视频帧号获取解码的视频数据
        :param frameId:
        :return:
        """
        # 首先从数据库中获取数据,如果数据库中没有该帧数据，则抛出异常
        try:
            zlib_data = self.redis_coon.get(frameId)
            try:
                frame = pickle.loads(zlib_data)
                return frame
            except:
                self.logger.error(f"{frameId} Decompress data fail, place check {zlib_data}")
                return None
        except:
            self.logger.error(f"Redis have not key {frameId} in datasets, in datasets have keys: {self.coon.keys()}")
            return None

    def del_except(self, taskId, sourcePaths, stateCode, stateDescribe):
        """
        发布异常结果信息
        :param taskId: 异常的任务ID
        :param sourcePaths: 异常的视频源
        :param stateCode: 异常的状态码
        :param stateDescribe: 异常的状态码描述信息
        :return:
        """
        except_data = {
            "puCode": self.puCode,
            "inputChannels": self.inputChannel,
            "outputChannels": self.outputChannel,
            "resultChannels": self.resultChannel,
            "puType": self.puType,
            "type": "ErrorState",
            "message": {
                "taskId": taskId,
                "sourcePaths": sourcePaths,
                "stateCode": stateCode,
                "stateDescribe": stateDescribe
            }
        }
        # 将数据转化为json格式数据,并将数据进行发布
        data = json.dumps(except_data)
        self.logger.error(f"异常信息{data}")
        self._publish(message=data, channel=self.registerChannel)

    def heartbeat(self, sleeptime=20):
        """
        对单元模块进行心跳检测(心跳检测模块使用单独的现场去实现, 定时的发布消息, 消息采用定时发布任务的机制，每分钟发布一次数据)
        :return:
        """
        while True:
            time.sleep(sleeptime)
            heartbeat_data = {
                "puCode": self.puCode,
                "inputChannels": self.inputChannel,
                "outputChannels": self.outputChannel,
                "resultChannels": self.resultChannel,
                "puType": self.puType,
                "type": "heartbeat"
            }
            # 将数据转化为json格式数据,并将数据进行发布
            data = json.dumps(heartbeat_data)
            # print(f"heartbeat_data = {heartbeat_data}")
            self._publish(message=data, channel=self.registerChannel)

    def subData(self, sub_queue, skip_frame=1):
        """
        订阅数据， 必要时需要进行抽帧处理
        在获取数据的时候我们首先需要基于配置文件提供的帧率判断数据是否需要进行抽帧处理，
        如果不需要抽帧处理则直接使用上一个处理单元的原市帧进行处理，如果需要抽帧处理，
        则基于需要的最小抽帧数进行抽帧处理。
        :param sub_queue:
        :return:
        """
        self.logger.info("==============================subData=====================================")
        subscribes = []
        for inputChannel in self.inputChannel:
            subscribes.append(self._subscribe(inputChannel))
        while True:
            for subscribe in subscribes:
                # 获取响应数据，并对获取的响应数据进行解码
                message = subscribe.parse_response()
                data_response = message[-1]
                data_response = json.loads(data_response)
                # 接收数据，判断接收到的数据是VIU数据，还是视频帧数据, 如果是视频帧数据，数据中会有关键字frameId
                if "frameId" in data_response.keys():
                    frameId = data_response["frameId"]
                    if frameId in self.data_sync:
                        self.data_sync[frameId].append(data_response)
                    else:
                        self.data_sync[frameId] = []
                        self.data_sync[frameId].append(data_response)
                    # 判断所有数据是否已经获取, 如果所有数据都已经获取，则将消息放入到队列，并将数据同步字典中的键值删除
                    if len(self.data_sync[frameId]) == len(self.inputChannel):
                        sync_data = self.data_sync.pop(frameId)
                        if frameId == "FF":
                            sub_queue.put(sync_data)
                        else:
                            frame_num = int(frameId.split("_")[-1])
                            if frame_num % skip_frame == 0:
                                sub_queue.put(sync_data)
                else:
                    self.logger.info(f"接收到视频源数据: {data_response}")
                    # 首先判断是摄像头首帧数据获取还是其他
                    if data_response["screenshot"] == "1":
                        # 对视频进行解码抽取首帧数据，并将首帧数据存储到固定位置发布给runtime
                        for url in data_response["sourcePaths"]:
                            cap = cv2.VideoCapture(url)
                            ret, frame = cap.read()
                            # 获取首帧图片文件夹地址
                            value_path = os.path.join(self.testPath, data_response["cameraId"] + "-" + data_response[
                                "deviceId"] + "-" + datetime.datetime.now().strftime('%Y%m%d'))
                            if not os.path.exists(value_path):
                                os.makedirs(value_path)
                            # 保存首帧图像
                            cv2.imwrite(os.path.join(value_path, data_response["cameraId"] + "-" + data_response[
                                "deviceId"] + ".jpg"), frame)
                            # 保存text文件
                            json_txt = {
                                "cameraId": data_response["cameraId"] + "-" + data_response["deviceId"],
                                "height": frame.shape[0],
                                "width": frame.shape[1]
                            }
                            with open(os.path.join(value_path, data_response["cameraId"] + "-" + data_response[
                                "deviceId"] + ".txt"), 'w', encoding='utf-8') as file:
                                file.write(json.dumps(json_txt))

                            # 将消息发布出去
                            camera_result = {"key": data_response["cameraId"], "messageId": json_txt['cameraId'],
                                             "type": "camera2Server", "value": value_path}
                            self.logger.info(f"发布首帧数据: {camera_result}")
                            self._publish(message=json.dumps(camera_result), channel="CameraTest")

                    # 判断任务是否停止(如果任务停止，则停止这个任务的所有视频)
                    if "switchCode" in data_response.keys():
                        if data_response["switchCode"] == "stop":
                            self.stop_data[data_response["parentTaskId"]] = data_response["sourcePaths"]
                            print(f"获取任务停止消息，需要停止任务{self.stop_data}")
                        else:
                            sub_queue.put([data_response])

    def perprocessing(self, sub_queue):
        """
        接收经过同步之后的订阅数据sub_queue，对数据进行抽帧，额外参数设置等预处理公共，预处理之后的图片暂存在缓存队列cache_queue,
        并将处理之后的数据存放到数据中心self.data_center
        :param sub_queue:
        :param skip_frame:
        :return:
        """
        self.logger.info("=======================================perprocessing=======================================")
        while True:
            # 获取经过数据同步之后的数据
            data_responses = sub_queue.get()
            # 获取经过同步的订阅数据，然后使用循环将每一帧数据发布出去
            for data_response in data_responses:
                print(f"接收到数据: {data_response['frameId']}")
                # 创建数据实例对象
                data = Data(data_response)
                frameId = data_response["frameId"]
                # 首先获取数据(如果数据失效，获取的数据是None)
                get_start_time = time.time()
                frame = self._get(frameId)
                get_end_time = time.time()
                # self.logger.info(f"获取数据耗时: {get_end_time - get_start_time}")
                # 获取该PU的超参数数据(该参数在Manage前端配置)
                parentTaskId = data_response['parentTaskId']
                if self.paramStatus:
                    parame_key = self.puCode + "_" + parentTaskId
                    parame = self.coon.get(parame_key)
                    print(parame)
                    self.param_queue.put(parame)
                    self.paramStatus = False

                data.image = frame
                self.pub_queue.put(data)

    def get_parame(self):
        if not self.param_queue.empty():
            return True, self.param_queue.get()
        else:
            return False, None

    def get(self):
        """
        第三方开发者获取数据的接口, 该方法主要是从队列中获取数据，调用一次获取一次数据
        :return: Data的实例化对象
        """
        data = self.pub_queue.get()
        return data

    def put(self, data):
        """
        第三方开发者发布数据的接口，通过该接口开发者将经过模型推理或者业务逻辑处理的数据发布出去
        :param data: Data类的实例化对象
        :return:
        """
        self.sub_queue.put(data)

    def default_dump(self, obj):
        """Convert numpy classes to JSON serializable objects."""
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def postprocessing(self):
        """
        将模型推理的结果或者业务逻辑处理的结果进行发布
        """
        # 发布帧结果信息
        pub_data = {
            'puType': self.puType,
            'puCode': self.puCode,
            'screenshot': "",
            'switchCode': "",
            'currentChannel': "",
            'parentTaskId': "",
            'sourcePaths': "",
            'traceFormworkId': "",
            'traceId': "",
            'taskId': "",
            'frameId': "",
            'timestamp': "",
            'output': {
                "detection": {}
            }
        }
        pub_start_time = time.time()
        while True:
            data = self.sub_queue.get()
            if isinstance(data, Data):
                pub_data["screenshot"] = data.screenshot
                pub_data["switchCode"] = data.switchCode
                pub_data["currentChannel"] = data.currentChannel
                pub_data["parentTaskId"] = data.parentTaskId
                pub_data["sourcePaths"] = data.sourcePaths
                pub_data["traceFormworkId"] = data.traceFormworkId
                pub_data["traceId"] = data.traceId
                pub_data["taskId"] = data.taskId
                pub_data["frameId"] = data.frameId
                pub_data["timestamp"] = data.timestamp
                pub_data["output"]["detection"] = data.detection
                start_time = time.time()
                self._publish(message=json.dumps(pub_data), channel=self.outputChannel[0])
                self.logger.info(f"发布数据: {pub_data}, 发布数据耗时: {time.time() - start_time}. 总耗时: {time.time() - pub_start_time}")
            else:
                # 首先是否生成业务事件(如果有业务数据生成，则先发布业务数据)
                if len(data["result"]["files"]) != 0:
                    # 将结果写入文件并将业务结果数据发布出去(将视频文件转移到指定文件夹下)
                    random_id = str(random.randint(100000, 999999))
                    messageId = data["taskId"] + random_id
                    type = "cloudResult2Server"
                    files = []
                    value_path = self.resultPath + data["taskId"] + "/" + self.puCode + "_" + random_id + "-" + \
                                 datetime.datetime.now().strftime('%Y%m%d')
                    if not os.path.exists(value_path):
                        os.makedirs(value_path)
                    print(f"files = {data['result']['files']}")
                    for result_data in data["result"]["files"]:
                        print(f"result_data = {result_data}")
                        shutil.move(result_data, value_path)
                        files.append(os.path.basename(result_data))
                    txt_info = {
                        "source": data["source"],
                        "taskId": data["taskId"],
                        "puCode": self.puCode,
                        "puType": self.puType,
                        "results": [
                            {"eventType": data["result"]["eventType"],
                             "files": files,
                             "startTime": data["result"]["startTime"],
                             "endTime": data["result"]["endTime"]}]
                    }

                    with open(os.path.join(value_path, self.puCode + "_" + random_id + ".txt"), 'w',
                              encoding='utf-8') as file:
                        file.write(json.dumps(txt_info))

                    # 发布业务结果数据
                    pub_event_result = {"messageId": messageId, "key": messageId, "value": value_path, "type": type}
                    self._publish(message=json.dumps(pub_event_result), channel=self.resultChannel)
                    self.logger.info(f"发布业务结果信息: {pub_event_result}, txt文件内容是: {txt_info}")

    def init(self):
        sub_queue = Queue(64)
        heartbeat_thread = threading.Thread(target=self.heartbeat)
        sub_thread = threading.Thread(target=self.subData, args=(sub_queue,))
        perprocess_thread = threading.Thread(target=self.perprocessing, args=(sub_queue,))
        postprocess_thread = threading.Thread(target=self.postprocessing, )
        heartbeat_thread.start()
        sub_thread.start()
        perprocess_thread.start()
        postprocess_thread.start()
