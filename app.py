import os
import time
import asyncio
import aiohttp
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Helper function to read URLs from the uploaded .txt file
def read_links_from_file(file_path):
    with open(file_path, 'r') as file:
        links = file.readlines()
    return [link.strip() for link in links]

# Helper function to write relevant URLs to a file
def write_relevant_urls_to_file(urls, output_file_path):
    with open(output_file_path, 'a') as file:
        for url in urls:
            file.write(url + "\n")

# Function to chunk a list into smaller batches
def chunk_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]

# Asynchronous function to check each URL for "horse" or "equine"
async def check_for_horse_or_equine_async(url, session):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                page_text = await response.text()
                if 'horse' in page_text.lower() or 'equine' in page_text.lower():
                    print(f"Found relevant content on: {url}")
                    return url
            else:
                print(f"Failed to retrieve {url}")
            return None
    except asyncio.TimeoutError:
        print(f"Timeout error for {url}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to process URLs in batches asynchronously
async def process_urls_in_batches(links, batch_size=10):
    # Create an aiohttp session for making async requests
    async with aiohttp.ClientSession() as session:
        # Split the URLs into smaller chunks (batches)
        for batch in chunk_list(links, batch_size):
            # Process each batch concurrently
            tasks = [check_for_horse_or_equine_async(url, session) for url in batch]
            results = await asyncio.gather(*tasks)  # Wait for all requests to complete

            # Filter out None values (URLs that don't contain relevant content)
            relevant_urls = [url for url in results if url]

            # Write the relevant URLs to a file
            if relevant_urls:
                write_relevant_urls_to_file(relevant_urls, 'relevant_urls.txt')
                print(f"Relevant URLs in this batch: {relevant_urls}")

            # Optional: sleep between batches to prevent overwhelming the server
            await asyncio.sleep(2)  # Sleep for 2 seconds between batches (optional)

# Flask route to handle file upload and URL processing
@app.route('/')
def index():
    return render_template('upload.html')

# Flask route to handle file upload and process URLs
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Save the uploaded file to a temporary directory
    filename = secure_filename(file.filename)
    uploaded_file_path = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(uploaded_file_path)

    # Read the links from the uploaded file
    links = read_links_from_file(uploaded_file_path)

    # Process the links asynchronously in batches
    asyncio.run(process_urls_in_batches(links, batch_size=10))  # Process in batches of 10

    # Provide the results file for download
    return send_file('relevant_urls.txt', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

