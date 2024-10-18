"""
title: Web Search using SearXNG and Scrape first N Pages
author: constLiakos with enhancements by justinh-rahb and ther3zz
funding_url: https://github.com/open-webui
version: 0.1.12
license: MIT
"""

import os
import requests
from datetime import datetime
import json
from requests import get
from bs4 import BeautifulSoup
import concurrent.futures
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import re
import unicodedata
from pydantic import BaseModel, Field
import asyncio
from typing import Callable, Any


class HelpFunctions:
    def __init__(self):
        pass

    def get_base_url(self, url):
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url

    def generate_excerpt(self, content, max_length=200):
        return content[:max_length] + "..." if len(content) > max_length else content

    def format_text(self, original_text):
        soup = BeautifulSoup(original_text, "html.parser")
        formatted_text = soup.get_text(separator=" ", strip=True)
        formatted_text = unicodedata.normalize("NFKC", formatted_text)
        formatted_text = re.sub(r"\s+", " ", formatted_text)
        formatted_text = formatted_text.strip()
        formatted_text = self.remove_emojis(formatted_text)
        return formatted_text

    def remove_emojis(self, text):
        return "".join(c for c in text if not unicodedata.category(c).startswith("So"))

    def process_search_result(self, result, valves):
        title_site = self.remove_emojis(result["title"])
        url_site = result["url"]
        snippet = result.get("content", "")

        # Check if the website is in the ignored list, but only if IGNORED_WEBSITES is not empty
        if valves.IGNORED_WEBSITES:
            base_url = self.get_base_url(url_site)
            if any(
                ignored_site.strip() in base_url
                for ignored_site in valves.IGNORED_WEBSITES.split(",")
            ):
                return None

        try:
            response_site = requests.get(url_site, timeout=20)
            response_site.raise_for_status()
            html_content = response_site.text

            soup = BeautifulSoup(html_content, "html.parser")
            content_site = self.format_text(soup.get_text(separator=" ", strip=True))

            truncated_content = self.truncate_to_n_words(
                content_site, valves.PAGE_CONTENT_WORDS_LIMIT
            )

            return {
                "title": title_site,
                "url": url_site,
                "content": truncated_content,
                "snippet": self.remove_emojis(snippet),
            }

        except requests.exceptions.RequestException as e:
            return None

    def truncate_to_n_words(self, text, token_limit):
        tokens = text.split()
        truncated_tokens = tokens[:token_limit]
        return " ".join(truncated_tokens)


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )


class Tools:
    class Valves(BaseModel):
        EX_LIBRIS_ENGINE_API_BASE_URL: str = Field(
            default="https://api-na.hosted.exlibrisgroup.com/primo/v1/search?apikey=l8xx91a2ae3e9fe648beb86725588a243b46&vid=01KSU_INST:NewUI&tab=Everything&scope=MyInst_and_CI",
            description="The base URL for Search Engine",
        )
        RETURNED_SCRAPPED_PAGES_NO: int = Field(
            default=3,
            description="The number of Search Results to Parse",
        )
        SCRAPPED_PAGES_NO: int = Field(
            default=5,
            description="Total pages scapped. Ideally greater than one of the returned pages",
        )
        PAGE_CONTENT_WORDS_LIMIT: int = Field(
            default=5000,
            description="Limit words content for each page.",
        )
        CITATION_LINKS: bool = Field(
            default=False,
            description="If True, send custom citations with links",
        )
        PC_AVAILABILITY: bool = Field (
            default=False,
            description="The PC Availabiliy"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    async def search_web(
        self,
        query: str,
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Search the web and get the content of the relevant pages. Search for unknown knowledge, news, info, public contact info, weather, etc.
        :params query: Web Query used in search engine.
        :return: The content of the pages in json format.
        """
        print("I made it to the search_web function")
        functions = HelpFunctions()
        emitter = EventEmitter(__event_emitter__)

        await emitter.emit(f"Initiating web search for: {query}")

        search_engine_url = self.valves.EX_LIBRIS_ENGINE_API_BASE_URL
        print(f"Search engine url: {search_engine_url}")
        params = {
            "q": f"any,contains,{query}",
            "format": "json",
            "pcAvailability": False
        }
        
        try:
            await emitter.emit("Sending request to search engine")
            resp = requests.get(
                search_engine_url, params=params, headers=self.headers, timeout=30
            )
            print(f"Query Results = {resp}")
            resp.raise_for_status()
            data = resp.json()
            await emitter.emit(f"Retrieved search results")

        except requests.exceptions.RequestException as e:
            await emitter.emit(
                status="error",
                description=f"Error during search: {str(e)}",
                done=True,
            )
            return json.dumps({"error": str(e)})

        await emitter.emit(
            status="complete",
            description=f"Web search completed. Retrieved content from 10 results",
            done=True,
        )

        return json.dumps(data, ensure_ascii=False)
    


