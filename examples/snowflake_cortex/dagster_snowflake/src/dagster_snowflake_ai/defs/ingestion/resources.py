"""Ingestion resources for web scraping."""

import re
import time
from datetime import datetime, timedelta
from urllib.error import URLError
from urllib.parse import urljoin, urlparse

import dagster as dg
import requests
from bs4 import BeautifulSoup

from dagster_snowflake_ai.defs.constants import (
    DEFAULT_HACKER_NEWS_MAX_PAGES,
    DEFAULT_MAX_CONTENT_LENGTH,
    DEFAULT_SCRAPE_TIMEOUT,
    MAX_CONTENT_LENGTH,
)


class WebScraperResource(dg.ConfigurableResource):
    """Resource for web scraping article content."""

    timeout: int = DEFAULT_SCRAPE_TIMEOUT
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    max_content_length: int = DEFAULT_MAX_CONTENT_LENGTH

    def scrape(self, url: str) -> str | None:
        """Scrape article content from URL."""
        if not self.is_valid_url(url):
            return None

        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()

            content_selectors = [
                "article",
                "main",
                '[role="main"]',
                ".content",
                ".post-content",
                ".article-content",
                "#content",
            ]

            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find("body")

            if not content:
                return None

            text = content.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            return text[: self.max_content_length] if text else None

        except (requests.RequestException, ValueError, AttributeError):
            return None

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except (AttributeError, ValueError):
            return False

    def parse_job_posting_row(self, row) -> dict | None:
        """Parse job posting row from Hacker News HTML."""
        try:
            title_cell = row.find("td", class_="title")
            if not title_cell:
                return None

            number_span = title_cell.find("span", class_="rank")
            job_number = None
            if number_span:
                job_number_text = number_span.get_text(strip=True)
                job_number = job_number_text.rstrip(".")

            titleline_span = title_cell.find("span", class_="titleline")
            if titleline_span:
                link_tag = titleline_span.find("a")
            else:
                link_tag = title_cell.find("a")

            if not link_tag:
                return None

            job_link = link_tag.get("href", "")
            if job_link:
                if not job_link.startswith("http"):
                    job_link = urljoin("https://news.ycombinator.com", job_link)

            company_text = link_tag.get_text(strip=True)

            domain = ""
            sitebit_span = title_cell.find("span", class_="sitebit")
            if not sitebit_span:
                if titleline_span:
                    sitebit_span = titleline_span.find("span", class_="sitebit")

            if sitebit_span:
                sitestr_span = sitebit_span.find("span", class_="sitestr")
                if sitestr_span:
                    domain = sitestr_span.get_text(strip=True)
                else:
                    domain_tag = sitebit_span.find("a")
                    if domain_tag:
                        domain = domain_tag.get_text(strip=True)

            time_text = ""
            job_id = None
            subtext_row = row.find_next_sibling("tr")
            if subtext_row:
                subtext_cell = subtext_row.find("td", class_="subtext")
                if subtext_cell:
                    age_tag = subtext_cell.find("span", class_="age")
                    if age_tag:
                        time_text = age_tag.get_text(strip=True)

                    item_link = subtext_cell.find("a", href=re.compile(r"item\?id=\d+"))
                    if item_link:
                        href = item_link.get("href", "")
                        match = re.search(r"item\?id=(\d+)", href)
                        if match:
                            job_id = match.group(1)

            return {
                "job_number": job_number,
                "job_id": job_id,
                "company": company_text,
                "link": job_link,
                "domain": domain,
                "time_posted": time_text,
                "full_posting": None,
            }
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Error parsing job row: {e}")
            return None

    def fetch_full_posting_content(self, url: str) -> str:
        """Fetch full content of job posting from URL."""
        if not self.is_valid_url(url):
            return ""

        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            content = ""

            main_content = (
                soup.find("main")
                or soup.find("article")
                or soup.find("div", class_=re.compile("content|post|job"))
            )
            if main_content:
                content = main_content.get_text(separator="\n", strip=True)
            else:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)

            return content[:MAX_CONTENT_LENGTH] if content else ""
        except Exception:
            return ""

    @staticmethod
    def parse_relative_time(time_str: str) -> datetime:
        """Parse relative time strings like '4 hours ago' into datetime."""
        time_str = time_str.lower().strip()
        now = datetime.now()

        patterns = [
            (r"(\d+)\s*minute", lambda m: now - timedelta(minutes=int(m.group(1)))),
            (r"(\d+)\s*hour", lambda m: now - timedelta(hours=int(m.group(1)))),
            (r"(\d+)\s*day", lambda m: now - timedelta(days=int(m.group(1)))),
            (r"(\d+)\s*week", lambda m: now - timedelta(weeks=int(m.group(1)))),
            (r"(\d+)\s*month", lambda m: now - timedelta(days=int(m.group(1)) * 30)),
        ]

        for pattern, func in patterns:
            match = re.search(pattern, time_str)
            if match:
                return func(match)

        return now

    def fetch_hackernews_job_postings(
        self,
        max_pages: int | None = DEFAULT_HACKER_NEWS_MAX_PAGES,
        context: dg.AssetExecutionContext | None = None,
    ) -> list[dict]:
        """Fetch job postings from Hacker News jobs page with pagination."""
        log = context.log if context else None

        base_url = "https://news.ycombinator.com/jobs"
        job_postings = []
        current_url = base_url
        pages_fetched = 0
        previous_url = None

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Cache-Control": "max-age=0",
            }
        )

        try:
            while current_url:
                if max_pages and pages_fetched >= max_pages:
                    if log:
                        log.info(f"Max pages ({max_pages}) reached. Stopping.")
                    break

                if previous_url:
                    session.headers["Referer"] = str(previous_url)
                else:
                    session.headers.pop("Referer", None)

                try:
                    if log:
                        log.info(f"Fetching page {pages_fetched + 1}: {current_url}")

                    response = session.get(str(current_url), timeout=self.timeout)
                    response.raise_for_status()
                    html = response.text
                    soup = BeautifulSoup(html, "html.parser")
                except requests.HTTPError as exc:
                    if exc.response.status_code == 403:
                        if log:
                            log.warning(
                                f"Got 403 Forbidden on page {pages_fetched + 1}. Stopping pagination. Fetched {len(job_postings)} jobs so far."
                            )
                        break
                    raise

                previous_url = current_url

                main_table = None
                for table in soup.find_all("table"):
                    if table.find("tr", class_=re.compile("athing")):
                        main_table = table
                        break

                if not main_table:
                    if log:
                        log.warning(
                            f"No table with job postings found on page {current_url}"
                        )
                    break

                job_rows = main_table.find_all("tr", class_=re.compile("athing"))
                if log:
                    log.info(
                        f"Found {len(job_rows)} job rows on page {pages_fetched + 1}"
                    )

                parsed_count = 0
                for row in job_rows:
                    job_data = self.parse_job_posting_row(row)
                    if job_data:
                        parsed_count += 1
                        if job_data["link"]:
                            job_data["full_posting"] = self.fetch_full_posting_content(
                                job_data["link"]
                            )
                        job_postings.append(job_data)

                if log:
                    log.info(
                        f"Parsed {parsed_count} job postings from {len(job_rows)} rows"
                    )

                pages_fetched += 1

                more_link: str | None = None
                morelink_tag = soup.find("a", class_="morelink")
                if morelink_tag:
                    href_attr = morelink_tag.get("href", "")
                    more_link = str(href_attr) if href_attr else None
                else:
                    # Find all links and check their text content
                    all_links = soup.find_all("a")
                    for link in all_links:
                        link_text = link.get_text(strip=True)
                        if link_text == "More":
                            href_attr = link.get("href", "")
                            href = str(href_attr) if href_attr else ""
                            if (
                                href.startswith("/jobs")
                                or "jobs" in href
                                or "next=" in href
                            ):
                                more_link = href
                                break

                if more_link:
                    if not more_link.startswith("http"):
                        current_url = urljoin("https://news.ycombinator.com", more_link)
                    else:
                        current_url = more_link

                    time.sleep(2)
                else:
                    if log:
                        log.info("No 'More' link found. Ending pagination.")
                    break

            if log:
                log.info(f"Total job postings fetched: {len(job_postings)}")
            return job_postings
        except requests.RequestException as exc:
            if log:
                log.error(f"Failed to fetch Hacker News job postings: {exc}")
            raise URLError(f"Failed to fetch Hacker News job postings: {exc}") from exc
        except Exception as exc:
            if log:
                log.error(f"Error parsing Hacker News job postings: {exc}")
            raise Exception(f"Error parsing Hacker News job postings: {exc}") from exc
        finally:
            session.close()

    def parse_story_row(self, row) -> dict | None:
        """Parse story row from Hacker News HTML."""
        try:
            title_cell = row.find("td", class_="title")
            if not title_cell:
                return None

            rank_span = title_cell.find("span", class_="rank")
            rank = None
            if rank_span:
                rank_text = rank_span.get_text(strip=True)
                rank = rank_text.rstrip(".")

            titleline_span = title_cell.find("span", class_="titleline")
            if titleline_span:
                link_tag = titleline_span.find("a")
            else:
                link_tag = title_cell.find("a")

            if not link_tag:
                return None

            story_url = link_tag.get("href", "")
            if story_url:
                if not story_url.startswith("http"):
                    story_url = urljoin("https://news.ycombinator.com", story_url)

            title_text = link_tag.get_text(strip=True)

            domain = ""
            sitebit_span = title_cell.find("span", class_="sitebit")
            if not sitebit_span:
                if titleline_span:
                    sitebit_span = titleline_span.find("span", class_="sitebit")

            if sitebit_span:
                sitestr_span = sitebit_span.find("span", class_="sitestr")
                if sitestr_span:
                    domain = sitestr_span.get_text(strip=True)
                else:
                    domain_tag = sitebit_span.find("a")
                    if domain_tag:
                        domain = domain_tag.get_text(strip=True)

            story_id = None
            points = None
            comments_count = None
            author = None
            time_text = ""

            subtext_row = row.find_next_sibling("tr")
            if subtext_row:
                subtext_cell = subtext_row.find("td", class_="subtext")
                if subtext_cell:
                    age_tag = subtext_cell.find("span", class_="age")
                    if age_tag:
                        time_text = age_tag.get_text(strip=True)

                    item_links = subtext_cell.find_all(
                        "a", href=re.compile(r"item\?id=\d+")
                    )
                    for item_link in item_links:
                        href = item_link.get("href", "")
                        match = re.search(r"item\?id=(\d+)", href)
                        if match:
                            story_id = match.group(1)
                            link_text = item_link.get_text(strip=True).lower()
                            if "comment" in link_text or "discuss" in link_text:
                                comments_match = re.search(
                                    r"(\d+)", item_link.get_text(strip=True)
                                )
                                if comments_match:
                                    comments_count = int(comments_match.group(1))
                                else:
                                    comments_count = 0
                            break

                    score_span = subtext_cell.find("span", class_="score")
                    if score_span:
                        score_text = score_span.get_text(strip=True)
                        points_match = re.search(r"(\d+)", score_text)
                        if points_match:
                            points = int(points_match.group(1))

                    author_link = subtext_cell.find("a", class_="hnuser")
                    if author_link:
                        author = author_link.get_text(strip=True)

            return {
                "story_id": story_id,
                "rank": rank,
                "title": title_text,
                "url": story_url,
                "domain": domain,
                "points": points,
                "author": author,
                "comments": comments_count,
                "time_posted": time_text,
            }
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Error parsing story row: {e}")
            return None

    def fetch_hackernews_stories(
        self,
        max_stories: int | None = None,
        story_type: str = "top",
        context: dg.AssetExecutionContext | None = None,
    ) -> list[dict]:
        """Fetch stories from Hacker News API (top/new/best)."""
        log = context.log if context else None

        api_base = "https://hacker-news.firebaseio.com/v0"

        story_endpoints = {
            "top": f"{api_base}/topstories.json",
            "new": f"{api_base}/newstories.json",
            "best": f"{api_base}/beststories.json",
        }

        if story_type not in story_endpoints:
            raise ValueError(
                f"Invalid story_type '{story_type}'. Must be one of: {list(story_endpoints.keys())}"
            )

        stories = []

        try:
            if log:
                log.info(f"Fetching {story_type} story IDs from Hacker News API...")

            response = requests.get(story_endpoints[story_type], timeout=self.timeout)
            response.raise_for_status()
            story_ids = response.json()

            if not isinstance(story_ids, list):
                raise ValueError(f"Expected list of story IDs, got {type(story_ids)}")

            if max_stories:
                story_ids = story_ids[:max_stories]

            if log:
                log.info(f"Found {len(story_ids)} story IDs. Fetching story details...")

            for idx, story_id in enumerate(story_ids):
                try:
                    item_url = f"{api_base}/item/{story_id}.json"
                    item_response = requests.get(item_url, timeout=self.timeout)
                    item_response.raise_for_status()
                    item_data = item_response.json()

                    if item_data and item_data.get("type") == "story":
                        story_text = item_data.get("text", "")
                        story_title = item_data.get("title", "")

                        story_dict = {
                            "story_id": str(item_data.get("id", "")),
                            "title": story_title,
                            "url": item_data.get("url", ""),
                            "points": item_data.get("score", 0),
                            "author": item_data.get("by", ""),
                            "comments": item_data.get("descendants", 0),
                            "time_posted": None,
                            "text": story_text,
                        }

                        if item_data.get("time"):
                            post_time = datetime.fromtimestamp(item_data.get("time"))
                            now = datetime.now()
                            delta = now - post_time

                            if delta.days > 0:
                                time_posted = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
                            elif delta.seconds >= 3600:
                                hours = delta.seconds // 3600
                                time_posted = (
                                    f"{hours} hour{'s' if hours > 1 else ''} ago"
                                )
                            elif delta.seconds >= 60:
                                minutes = delta.seconds // 60
                                time_posted = (
                                    f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                                )
                            else:
                                time_posted = "just now"

                            story_dict["time_posted"] = time_posted

                        if story_dict["url"]:
                            try:
                                parsed = urlparse(story_dict["url"])
                                story_dict["domain"] = parsed.netloc.replace("www.", "")
                            except Exception:
                                story_dict["domain"] = ""
                        else:
                            story_dict["domain"] = ""

                        stories.append(story_dict)

                    if (idx + 1) % 10 == 0:
                        time.sleep(0.1)

                except requests.RequestException as exc:
                    if log:
                        log.warning(f"Failed to fetch story {story_id}: {exc}")
                    continue
                except Exception as exc:
                    if log:
                        log.warning(f"Error processing story {story_id}: {exc}")
                    continue

            if log:
                log.info(
                    f"Successfully fetched {len(stories)} stories from Hacker News API"
                )

            return stories

        except requests.RequestException as exc:
            if log:
                log.error(f"Failed to fetch Hacker News stories from API: {exc}")
            raise URLError(
                f"Failed to fetch Hacker News stories from API: {exc}"
            ) from exc
        except Exception as exc:
            if log:
                log.error(f"Error processing Hacker News stories: {exc}")
            raise Exception(f"Error processing Hacker News stories: {exc}") from exc
