import requests
from bs4 import BeautifulSoup
from typing import List
import time
from langchain_core.documents import Document
import dagster as dg

class SitemapScraper(dg.ConfigurableResource):
    sitemap_url : str
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
        
    def parse_sitemap(self) -> List[str]:
        """Extract URLs from sitemap XML"""
        response = requests.get(self.sitemap_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'xml')
        
        urls = []
        # Find all loc elements within url elements
        for loc in soup.find_all('loc'):
            if loc.text.strip():
                urls.append(loc.text.strip())
                
        print(f"Found {len(urls)} URLs in sitemap")
        return urls
    
    def scrape_page(self, url: str) -> Document:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            title = soup.title.string if soup.title else ''
            main_content = soup.find('main') or soup.find('article') or soup.body
            
            if main_content:
                content = []
                for elem in main_content.stripped_strings:
                    if elem.strip():
                        content.append(elem.strip())
                text_content = '\n'.join(content)
            else:
                text_content = '\n'.join(s.strip() for s in soup.stripped_strings if s.strip())

            return Document(
                page_content=text_content,
                metadata={
                    "source": url,
                    "title": title
                }
            )
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def get_documents(self, limit: int = None) -> List[Document]:
        urls = self.parse_sitemap()
        if limit:
            urls = urls[:limit]
        
        documents = []
        for i, url in enumerate(urls, 1):
            print(f"Scraping {i}/{len(urls)}: {url}")
            doc = self.scrape_page(url)
            if doc:
                documents.append(doc)
            time.sleep(1.0)
            
        return documents

scraper_resource = SitemapScraper(sitemap_url=dg.EnvVar("DOCS_SITEMAP"))