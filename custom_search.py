import os
import requests
from typing import Callable, Any
from pydantic import BaseModel, Field
import json

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
    async def message(self,data):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "message",
                    "data": {"content": data}
                }
            )

class Tools:
    class Valves(BaseModel):
        EX_LIBRIS_API_BASE_URL: str = Field(
            default="https://api-na.hosted.exlibrisgroup.com/primo/v1/search",
            description="The base URL for Ex Libris Search Engine",
        )
        EX_LIBRIS_API_KEY: str = Field(
            default="l8xx91a2ae3e9fe648beb86725588a243b46",
            description="Ex Libris Search API Key",
        )
        EX_LIBRIS_VID: str = Field(
            default="01KSU_INST:NewUI",
            description="Set View",
        )
        EX_LIBRIS_TAB: str = Field(
            default="Everything",
            description="Tab Parameter",
        )
        EX_LIBRIS_SCOPE: str = Field(
            default="MyInst_and_CI",
            description="Scope of search",
        )
        EX_LIBRIS_FORMAT: str = Field (
            default="json",
            description="Response format"
        )
        EX_LIBRIS_QUERY_COL: str = Field (
            default="any",
            description="First q parameter"
        )
        EX_LIBRIS_QUERY_OP: str = Field (
            default="contains",
            description="Field search operator"
        )
        EX_LIBRIS_PC_AVAIL: str = Field (
            default="false",
            description="The PC Availability"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

    async def search_exlibris (
        self,
        query: str,
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Search K-State's Ex Libris search api for Books, Journals, Articles, and more.
        :params query: Web Query used in search engine.
        :return: The content of the page in json format.
        """
        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Initiating web search for: {query}")
        base_url = self.valves.EX_LIBRIS_API_BASE_URL
        params = {
            "apikey": self.valves.EX_LIBRIS_API_KEY,
            "vid": self.valves.EX_LIBRIS_VID,
            "tab": self.valves.EX_LIBRIS_TAB,
            "scope": self.valves.EX_LIBRIS_SCOPE,
            "format": self.valves.EX_LIBRIS_FORMAT,
            "q": f"{self.valves.EX_LIBRIS_QUERY_COL},{self.valves.EX_LIBRIS_QUERY_OP},{query}",
            "pcAvailability": self.valves.EX_LIBRIS_PC_AVAIL
        }

        try:
            await emitter.emit(f"Sending request to Ex Libris search to: {base_url}")
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"Search Response: {data}")

            await emitter.emit(
            status="complete",
            description=f"Web search completed.Finishing up...",
            done=True,
            )
            results = []
            for r in data['docs']:
                results.append(
                    {
                        "link": r['pnx']['links']['linktohtml']
                    }
                )
            print(results)
            await emitter.message(json.dump(results))
            return json.dump(results)
        except requests.RequestException as e:
            await emitter.message(str(e))
            return f"Error fetching data: {str(e)}"


