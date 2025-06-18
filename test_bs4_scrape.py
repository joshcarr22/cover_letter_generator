import requests
from bs4 import BeautifulSoup

url = "https://www.seek.com.au/job/84825118"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.seek.com.au/"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

print(response.text[:2000])

print(soup.get_text()[:2000])  # Print first 2000 chars of raw text 

print("Help us keep SEEK secure, confirm you are human. Enable JavaScript and cookies to continue") 