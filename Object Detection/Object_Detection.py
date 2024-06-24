import argparse
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utilss import visualize
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from threading import Thread
import websockets
import asyncio
import base64

cred = credentials.Certificate("key.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://arm4-acb76-default-rtdb.firebaseio.com/'
})

# Reference to the specific part of your database
ref = db.reference('/')

# Global variables to calculate FPS
COUNTER, FPS = 0, 0
START_TIME = time.time()

# Global detection result list and frame
detection_result_list = []
detection_frame = None

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def save_result(result: vision.ObjectDetectorResult, unused_output_image: mp.Image, timestamp_ms: int):
    global FPS, COUNTER, START_TIME, detection_result_list
    # Calculate the FPS
    if COUNTER % 10 == 0:
        FPS = 10 / (time.time() - START_TIME)
        START_TIME = time.time()
    detection_result_list.append(result)
    COUNTER += 1

def capture_frames(camera_id, frame_width, frame_height):
    global detection_frame, detection_result_list, FPS

    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    time.sleep(2)

    while True:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.resize(image, (640, 480))
        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        detector.detect_async(mp_image, time.time_ns() // 1_000_000)

        if detection_result_list:
            for detection_result in detection_result_list:
                for detection in detection_result.detections:
                    origin_x = detection.bounding_box.origin_x
                    origin_y = detection.bounding_box.origin_y
                    label = detection.categories[0].category_name
                    print('x_coordinate : ', origin_x)
                    print('y_coordinate : ', origin_y)
                    print('label        : ', label)
                    x = map_value(origin_x, 1, 640, 0, 20)
                    y = map_value(origin_y, 6.5, 480, 0, 20)
                    
                    data = {
                    'origin_x': round(x, 2),
                    'origin_y': round(y, 2),
                    'Label': label
                        }

                    # Push data to the database
                    ref.set(data)

            image = visualize(image, detection_result_list[0])
            detection_result_list.clear()

        # Display FPS on the frame
        cv2.putText(image, f"FPS: {FPS:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        detection_frame = image

        if detection_frame is not None:
            cv2.imshow('object_detection', detection_frame)

        if cv2.waitKey(1) == 27:  # ESC key
            break
            

def generate_frames():
    global detection_frame
    while True:
        if detection_frame is not None:
            ret, buffer = cv2.imencode('.jpg', detection_frame)
            if ret:
                frame = buffer.tobytes()
                yield frame
        else:
            time.sleep(0.1)

async def transmit(websocket, path):
    print("Client Connected!")
    try:
        for frame in generate_frames():
            data = base64.b64encode(frame).decode('utf-8')
            await websocket.send(data)
    except websockets.ConnectionClosed as e:
        print("Client Disconnected!")

def run(model: str, max_results: int, score_threshold: float, cam_id: int, width: int, height: int) -> None:
    global detector

    base_options = python.BaseOptions(model_asset_path=model)
    options = vision.ObjectDetectorOptions(base_options=base_options,
                                           running_mode=vision.RunningMode.LIVE_STREAM,
                                           max_results=max_results, score_threshold=score_threshold,
                                           result_callback=save_result)
    detector = vision.ObjectDetector.create_from_options(options)

    # Start a thread for frame capturing
    capture_thread = Thread(target=capture_frames, args=(cam_id, width, height), daemon=True)
    capture_thread.start()

    # Start the WebSocket server
    start_server = websockets.serve(transmit, host="0.0.0.0", port=5000, ping_interval=10, ping_timeout=5)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', help='Path of the object detection model.', required=False, default='Custom_Model.tflite')
    parser.add_argument('--maxResults', help='Max number of detection results.', required=False, default=5)
    parser.add_argument('--scoreThreshold', help='The score threshold of detection results.', required=False, type=float, default=0.25)
    parser.add_argument('--cameraId', help='Id of camera.', required=False, type=int, default=0)
    parser.add_argument('--frameWidth', help='Width of frame to capture from camera.', required=False, type=int, default=640)
    parser.add_argument('--frameHeight', help='Height of frame to capture from camera.', required=False, type=int, default=480)
    args = parser.parse_args()

    run(args.model, int(args.maxResults), args.scoreThreshold, int(args.cameraId), args.frameWidth, args.frameHeight)

if __name__ == '__main__':
    main()
