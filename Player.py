import cv2
from threading import Thread, Semaphore, Lock

STOP = 123
DELAY = 42
FILE = 'clip.mp4'


class ProducerConsumerQ:

    def __init__(self):
        self.queue = []
        self.full = Semaphore(0)
        self.empty = Semaphore(10)
        self.lock = Lock()

    def put(self, item):  # Producer
        self.empty.acquire()
        self.lock.acquire()
        self.queue.append(item)
        self.lock.release()
        self.full.release()

    # Question
    def get(self):  # Consumer
        self.full.acquire()
        self.lock.acquire()
        frame = self.queue.pop(0)
        self.lock.release()
        self.empty.release()
        return frame


# Extract frame from file
def extract_frames(file_name, output_q):
    count = 0
    # Load file
    vid_cap = cv2.VideoCapture(file_name)
    # Read frame
    success, image = vid_cap.read()

    while success:
        output_q.put(image)
        success, image = vid_cap.read()
        print(f'Reading frame {count} {success}')
        count += 1

    # Indicates when extraction complete
    output_q.put(STOP)
    print('Frame extraction complete')


# Convert colored frames into grayscale
def convert_grayscale(input_q, output_q):
    count = 0
    input_frame = input_q.get()

    while type(input_frame) != int:
        print(f'Converting frame {count}')
        grayscale_frame = cv2.cvtColor(input_frame, cv2.COLOR_BGR2GRAY)
        output_q.put(grayscale_frame)
        count += 1
        input_frame = input_q.get()

    # Indicates when conversion complete
    output_q.put(STOP)
    print('Frame conversion complete')
    return


# Displays frames using cv2.imshow()
def display_frames(input_q):
    count = 0
    input_frame = input_q.get()

    while type(input_frame) != int:
        print(f'Displaying frame {count}')
        cv2.imshow('Video', input_frame)
        if cv2.waitKey(DELAY) and 0xFF == ord("q"):
            break

        count += 1
        input_frame = input_q.get()

    print('Finished displaying all frames')
    cv2.destroyAllWindows()


# Creating producer and consumer "pipelines"
extract_to_grayscale_q = ProducerConsumerQ()
grayscale_to_display_q = ProducerConsumerQ()

extract = Thread(target=extract_frames, args=(FILE, extract_to_grayscale_q))
convert = Thread(target=convert_grayscale, args=(extract_to_grayscale_q, grayscale_to_display_q))
display = Thread(target=display_frames, args=(grayscale_to_display_q,))

extract.start()
convert.start()
display.start()

