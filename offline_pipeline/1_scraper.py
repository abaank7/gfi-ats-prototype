import os
from scrapling.fetchers import FetcherSession
from data.resume_links import RESUMES_LINKS



def run_scraper():

    output_dir = os.path.join("offline_pipeline", "raw_resumes")
    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    fail_count = 0

    print("🚀 Initializing Scrapling Stealth Fetcher...")

    with FetcherSession(impersonate="chrome") as session:
        for filename, view_url in RESUMES_LINKS.items():

            download_url = view_url.replace("/file/", "/download/")
            file_path = os.path.join(output_dir, filename)

            if os.path.exists(file_path):
                print(f"⏭️  Skipping {filename} (Already exists)")
                continue

            print(f"📥 Fetching: {filename}...")

            try:
                response = session.get(download_url)
                if response.content.startswith(b"PK"):
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Saved correctly: {filename}")
                    success_count += 1
                else:
                    print(
                        f"❌ Failed validation for {filename}. Zoho returned unexpected data (possibly an HTML bot challenge)."
                    )
                    fail_count += 1

            except Exception as e:
                print(f"⚠️ Network error on {filename}: {e}")
                fail_count += 1

    print("\n--- 🏁 Scraping Complete ---")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed/Blocked: {fail_count}")


if __name__ == "__main__":
    run_scraper()
