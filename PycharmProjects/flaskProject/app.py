from urllib import response as urllib_response
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin
import concurrent.futures
import os
import threading

import time

app = Flask(__name__)


def extract_content(url, extract_links=False, extract_images=False):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    extracted_data = []

    if extract_links:
        extracted_links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        extracted_data.append(('Links', extracted_links))

    if extract_images:
        extracted_images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
        extracted_data.append(('Images', extracted_images))
    return extracted_data

# use Python's CSV module to write a list of rows to a CSV file named 'output.csv'.

def write_to_csv(data, filename='output.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(data)

# Downloads URL-based files to destination folder.
def download_file(url, destination_folder):
    response = requests.get(url)
    file_name = os.path.join(destination_folder, os.path.basename(url))

    with open(file_name, 'wb') as file:
        file.write(response.content)

    print(f"Downloaded {url} to {file_name}")


class DownloadThread(threading.Thread):
    def __init__(self, url, destination_folder, headers=None):
        super(DownloadThread, self).__init__()
        self.url = url
        self.destination_folder = destination_folder
        self.headers = headers
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.paused = False
        self.start_time = time.time()
        self.downloaded_bytes = 0

    def run(self):
        download_file(self.url, self.destination_folder)
        response = requests.get(self.url, stream=True)
        file_name = os.path.join(self.destination_folder, os.path.basename(self.url))

        with open(file_name, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if self.stop_event.is_set():
                    break
                if not self.pause_event.is_set():
                    file.write(chunk)
                    self.downloaded_bytes += len(chunk)
                else:
                    self.paused = True

    def pause(self):
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()

    def get_statistics(self):
        elapsed_time = time.time() - self.start_time
        download_speed = self.downloaded_bytes / (1024 * elapsed_time) if elapsed_time > 0 else 0
        remaining_time = (urllib_response.headers.get('content-length', 0) - self.downloaded_bytes) / download_speed \
            if download_speed > 0 else 0
        return {
            'download_speed': download_speed,
            'remaining_time': remaining_time,
            'downloaded_bytes': self.downloaded_bytes
        }


# this function of code help in parallel downloads.
def parallel_downloads(urls, destination_folder, num_parallel_downloads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_parallel_downloads) as executor:
        futures = [executor.submit(download_file, url, destination_folder) for url in urls]
        concurrent.futures.wait(futures)


def crawl(url, max_depth, current_depth=0, visited=None):
    if visited is None:
        visited = set()

    if current_depth > max_depth:
        return

    if url not in visited:
        visited.add(url)
        extracted_data = extract_content(url, extract_links=True, extract_images=True)
        write_to_csv(extracted_data)

        for link in extract_links_from_url(url):
            crawl(link, max_depth, current_depth + 1, visited)

# this code help to URL GET request and storage of response & using beautifulSoup to parse response HTML.
def extract_links_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = response.url

    links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]
    return links


def create_directory(destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']

        extract_links = 'extract_links' in request.form
        extract_images = 'extract_images' in request.form

        extracted_data = extract_content(url, extract_links, extract_images)

        if extracted_data:
            if extract_images:
                image_urls = extracted_data[-1][1]
                destination_folder = os.path.join(app.root_path, 'static', 'images')
                create_directory(destination_folder)
                parallel_downloads(image_urls, destination_folder, num_parallel_downloads=5)
            write_to_csv(extracted_data)
            return render_template('result.html', data=extracted_data)
        else:
            return "No data extracted."

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
