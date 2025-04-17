import requests
import os

output_folder = "static"
os.makedirs(output_folder, exist_ok=True)

images = {
    "demo.jpg": "https://images.unsplash.com/photo-1501959915551-4e8d63e34c11?auto=format&fit=crop&w=640&q=80",
    "demo2.jpg": "https://images.unsplash.com/photo-1629904853716-f0bc54f7bdfd?auto=format&fit=crop&w=640&q=80",
    "selfie.jpg": "https://images.unsplash.com/photo-1626908013358-b84a64af9da4?auto=format&fit=crop&w=640&q=80"
}

for filename, url in images.items():
    print(f"Downloading {filename}...")
    res = requests.get(url)
    if res.status_code == 200:
        with open(os.path.join(output_folder, filename), "wb") as f:
            f.write(res.content)
        print(f"{filename} saved.")
    else:
        print(f"Failed to download {filename}. Status: {res.status_code}")
