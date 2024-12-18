import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, send_from_directory, render_template

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Ensure the folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to read links from a text file
def read_links_from_file(file_path):
    with open(file_path, 'r') as file:
        links = file.readlines()
    return [link.strip() for link in links]  # Remove any extra whitespace or newline characters

# Function to prepend 'http://' to links starting with 'www.'
def normalize_url(url):
    if url.startswith("www."):
        return "http://" + url
    return url  # Return the link as is if it's already a full URL (e.g., http:// or https://)

# Function to check the content of the webpage for "horse" or "equine"
def check_for_horse_or_equine(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            if 'horse' in page_text or 'equine' in page_text:
                return True
            return False
        return False
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return False

# Function to write URLs with relevant content to a text file
def write_relevant_urls_to_file(urls, output_file):
    with open(output_file, 'w') as file:
        for url in urls:
            file.write(url + '\n')

# Function to process the uploaded file and find relevant URLs
def scrape_links(file_path, output_file):
    links = read_links_from_file(file_path)
    relevant_urls = []

    for link in links:
        normalized_link = normalize_url(link)
        if check_for_horse_or_equine(normalized_link):
            relevant_urls.append(normalized_link)

    if relevant_urls:
        write_relevant_urls_to_file(relevant_urls, output_file)
        return output_file
    return None

# Route to upload file
@app.route('/')
def upload_form():
    return render_template('upload.html')

# Route to handle the file upload and processing
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    if file and file.filename.endswith('.txt'):
        # Save the uploaded file
        uploaded_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(uploaded_file_path)

        # Process the file and generate the output
        output_file_path = os.path.join(OUTPUT_FOLDER, 'relevant_urls.txt')
        result_file = scrape_links(uploaded_file_path, output_file_path)

        if result_file:
            # Provide the download link for the processed file
            return render_template('download.html', output_file=result_file)

        return "No relevant URLs found.", 400

    return "Invalid file type. Only .txt files are allowed.", 400

# Route to serve the processed output file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

