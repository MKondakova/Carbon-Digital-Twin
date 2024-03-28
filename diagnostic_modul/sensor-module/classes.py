from queue import Queue
from torch import Tensor
from typing import Union, List
from enum import Enum
import numpy as np
import cv2
import datetime
from PIL import Image
from ultralytics import YOLO
from threading import Thread
import time
import sqlite3
import sys
import logging

import json
import random

# logger = logging.getLogger('main_logger')
# logger.setLevel(logging.DEBUG)

# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(formatter)

# logger.addHandler(console_handler)

WEIGHTS_DEFECTS = {
    0: 0.05,
}

# class TypingSource(Enum):
#     VIDEO = 0
#     OTHER = 1

def create_database():
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INT NOT NULL,
                prediction REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        return False

    return True

class Handler:
    def __init__(self):
        self.sources = []
        self.models = []
        self.queue = Queue()
        self.source_model_mapping = {}
        self.polling_interval = 10
        # logger.info('Инициализация обработчика')


    def add_source_model_mapping(self, source, model):
        self.sources.append(source)
        self.models.append(model)
        self.source_model_mapping[source.id] = model

    def polling_sensors(self) -> int:
        data = {}
        for source in self.sources:
            # logger.debug(f'Получаю данные с камеры {source.id}')
            data[source.id] = source.get_value()
        return data

    def polling_sensors_async(self) -> None:
        try:
            while True:
                # logger.info('Опрос камеры')
                data = self.polling_sensors()
                self.queue.put(data)
                # logger.debug(self.queue.empty())
                time.sleep(self.polling_interval)
        except Exception as e:
            print(f"Error in polling_sensors_async: {e}")
            sys.exit(1)

    def value_predict(self, source_id: int, source_value: Image) -> dict:
        model = self.source_model_mapping.get(source_id)
        if model:
            result = model.predict(source_value)
            return {source_id: result}
        else:
            return {}

    # Пока записываем в тестовую
    def write_db_request(self, source_id: int, prediction: float) -> int:
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO predictions (source_id, prediction) VALUES (?, ?)
            ''', (source_id, prediction))

            conn.commit()
            conn.close()
            return 0
        except Exception as e:
            print(f"Error writing to database: {e}")
            return 0
        
    def processing_values(self, defects: List[dict]):
        if len(defects) == 0:
            return 0
        else:
            return np.mean([WEIGHTS_DEFECTS[x['class_']] * x['confidence_'] for x in defects])


    def run(self) -> None:
        try:
            poll_thread = Thread(target=self.polling_sensors_async)
            poll_thread.start()

            while True:
                if not self.queue.empty():
                    # logger.info("Обрабатываем модель")
                    data = self.queue.get()
                    for source_id, source_value in data.items():
                        model_result = self.value_predict(source_id, source_value)
                        if model_result:
                            defects = []
                            for r in model_result[source_id]:
                                for b in r.boxes:
                                    # logger.debug(f'Найден дефект класса {int(b.cls)} с вероятногсть {float(b.conf)}')
                                    defects.append({'class_': int(b.cls), 'confidence_': float(b.conf)})
                            self.write_db_request(source_id, self.processing_values(defects))
                            
                            
        except Exception as e:
            # logger.error(f"Error in run: {e}")
            poll_thread.join()
            sys.exit(1)

class Source:
    def __init__(self, id, unit, number, address):
        self.id = id
        self.unit = unit
        self.number = number
        self.address = address

    def get_value(self) -> Image:
        # logger.debug(f'Обращение к камере {self.id}')
        cap = cv2.VideoCapture(self.address)
        if not cap.isOpened():
            # logger.debug('Нет доступа к камере')
            exit()

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        random_frame_index = random.randint(0, total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_index)

        ret, frame = cap.read()
        data = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        # logger.info(data)
        return data

class Model:
    def __init__(self, version: str, path: str):
        self.version = version
        self.path = path
    
    def predict(self, frame: Image) -> Tensor:
        model = YOLO(self.path)
        results = model(frame)
        return results