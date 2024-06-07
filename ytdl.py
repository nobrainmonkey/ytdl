import os
from pytube import YouTube
import PySimpleGUI as sg
import threading
import queue

# Global variables for window and queue
window = None
output_queue = queue.Queue()

# Callback functions to update the GUI with the current download status
def on_start(stream):
    title = stream.title
    output_queue.put(f"开始下载 {title}\n")

def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent_complete = bytes_downloaded / total_size * 100
    output_queue.put(f"正在下载：{bytes_downloaded/1048576:.2f} mb/ {total_size/1048576:.2f} mb ({percent_complete:.2f}%)\n")
    window.write_event_value('-PROGRESS-', percent_complete)

def on_complete(stream, file_path):
    stream_title = stream.title
    output_queue.put(f"{stream_title} 下载完成!\n")

# Function to handle individual video download
def download_from_url(url, local_path="."):
    try:
        yt = YouTube(url, on_progress_callback=on_progress, on_complete_callback=on_complete)
        download_stream = yt.streams.get_highest_resolution()
        on_start(download_stream)
        output_file = os.path.join(local_path, download_stream.default_filename)
        
        # Overwrite existing files
        if os.path.exists(output_file):
            os.remove(output_file)
        
        # Download file
        download_stream.download(output_path=local_path)
    except Exception as e:
        output_queue.put(f"下载失败: {e}\n")

# Function to download multiple videos
def batch_download(url_list, local_path="."):
    if not os.path.exists(local_path):
        os.mkdir(local_path)
    for url in url_list:
        window['-PROGRESS-'].update_bar(0)  # Reset progress bar for each download
        download_from_url(url, local_path=local_path)
    output_queue.put("下载完成")

# Function to read URL list from a text file
def get_url_list_from_file(input_file):
    url_list = []
    with open(input_file, "r") as file:
        url_list = file.readlines()
    url_list = [url.rstrip('\n') for url in url_list if url.rstrip('\n')]
    return url_list

# Function to run the download in a separate thread
def download_thread(url_list, local_path):
    batch_download(url_list, local_path)

# Main function to create and run the GUI
def main():
    sg.theme('DarkBlue')

    layout = [
        [sg.Text("选择包含视频地址的文本文件:", size=(25, 1), font=("Helvetica", 14))],
        [sg.InputText(size=(50, 1), font=("Helvetica", 14), key='-FILE-'), sg.FileBrowse("浏览", file_types=(("Text Files", "*.txt"),), font=("Helvetica", 14))],
        [sg.Text("输入单个视频地址:", size=(25, 1), font=("Helvetica", 14))],
        [sg.InputText(size=(50, 1), font=("Helvetica", 14), key='-URL-')],
        [sg.Text("选择下载路径:", size=(25, 1), font=("Helvetica", 14))],
        [sg.InputText(default_text=os.getcwd(), key="-FOLDER-", size=(50, 1), font=("Helvetica", 14)), sg.FolderBrowse("浏览", font=("Helvetica", 14))],
        [sg.Button("开始下载", size=(12, 1), font=("Helvetica", 14)), sg.Button("退出", size=(12, 1), font=("Helvetica", 14))],
        [sg.ProgressBar(max_value=100, orientation='h', size=(60, 20), key='-PROGRESS-', expand_x=True)],
        [sg.Multiline(size=(80, 20), key='-OUTPUT-', autoscroll=True, disabled=True, expand_x=True, expand_y=True, font=("Helvetica", 14))]
    ]

    global window
    window = sg.Window("YouTube视频下载器", layout, resizable=True, finalize=True, size=(1000, 600))

    while True:
        event, values = window.read()
        
        if event in (sg.WINDOW_CLOSED, "退出"):
            break
        if event == "开始下载":
            input_file = values['-FILE-']
            local_path = values["-FOLDER-"]
            single_url = values["-URL-"]
            if not input_file and not single_url:
                sg.popup("请选择包含视频链接的文本文件或输入单个视频链接")
                continue
            if input_file:
                url_list = get_url_list_from_file(input_file)
            else:
                url_list = [single_url]
            window['-OUTPUT-'].update('')
            threading.Thread(target=download_thread, args=(url_list, local_path), daemon=True).start()
        
        # Check the queue for messages and update the output element
        while not output_queue.empty():
            message = output_queue.get()
            window['-OUTPUT-'].print(message)
        
        # Update the progress bar
        if event == '-PROGRESS-':
            percent_complete = values['-PROGRESS-']
            window['-PROGRESS-'].update_bar(percent_complete)

    window.close()

if __name__ == "__main__":
    main()
