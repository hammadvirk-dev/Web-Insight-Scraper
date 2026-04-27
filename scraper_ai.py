```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
import google.generativeai as genai
import os
import time
import json

# Configuration
# Note: The environment provides the API key at runtime.
apiKey = ""

def setup_gemini():
    """Initializes the Gemini API with exponential backoff."""
    genai.configure(api_key=apiKey)
    return genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')

def get_web_content(url):
    """Scrapes headings and links from the target URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extracting common elements
        data = []
        
        # Capture Headings
        for tag in ['h1', 'h2', 'h3']:
            for item in soup.find_all(tag):
                text = item.get_text(strip=True)
                if text:
                    data.append({"type": tag, "content": text})
        
        # Capture Links/Titles
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if text:
                data.append({"type": "link", "content": text, "url": link['href']})
                
        return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def analyze_with_ai(data_summary):
    """Sends scraped data to Gemini for trend analysis."""
    model = setup_gemini()
    
    prompt = f"""
    You are a professional Market Analyst. Below is raw scraped data from a website:
    {data_summary}
    
    Task:
    1. Categorize the findings into logical business sectors.
    2. Identify the 'Most Important Trends' visible in this data.
    3. Provide actionable insights for a market analyst.
    4. Format the output in professional Markdown.
    """
    
    # Exponential Backoff Implementation
    for delay in [1, 2, 4, 8, 16]:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            time.sleep(delay)
    
    return "AI Analysis failed after multiple retries."

def main():
    target_url = input("Enter the URL to scrape: ")
    print(f"🔍 Scraping {target_url}...")
    
    scraped_data = get_web_content(target_url)
    
    if scraped_data:
        # Save Raw Data to CSV
        df = pd.DataFrame(scraped_data)
        df.to_csv("scraped_raw_data.csv", index=False)
        print("✅ Raw data saved to scraped_raw_data.csv")
        
        # Prepare data for AI
        summary_text = "\n".join([f"{item['type']}: {item['content']}" for item in scraped_data[:50]]) # Limit context
        
        print("🧠 Analyzing trends with Gemini AI...")
        insights = analyze_with_ai(summary_text)
        
        # Save Insights to Markdown
        with open("AI_INSIGHTS.md", "w", encoding="utf-8") as f:
            f.write(f"# Market Insights for {target_url}\n\n")
            f.write(insights)
        
        print("✅ AI Insights saved to AI_INSIGHTS.md")
    else:
        print("❌ Failed to retrieve content.")

if __name__ == "__main__":
    main()

```

