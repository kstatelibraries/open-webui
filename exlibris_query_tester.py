import asyncio
import requests
import json

# Mock emitter class with async emit and message methods
class Emitter:
    async def emit(self, message=None, status=None, description=None, done=None):
        print(f"Emitting message: {message}, status: {status}, description: {description}, done: {done}")

    async def message(self, msg):
        print(f"Sending message: {msg}")

# Function to simulate the search request
async def search_request(emitter, base_url, params):
    try:
        # Emit starting message
        await emitter.emit(f"Sending request to Ex Libris search to: {base_url}")
        
        # Perform the HTTP GET request to the search endpoint
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses (e.g., 4xx/5xx)

        # Parse JSON response
        data = response.json()
        print(f"Search Response: {data}")

        # Emit completion message
        await emitter.emit(
            status="complete",
            description="Web search completed. Finishing up...",
            done=True,
        )

        # Extract results from the response
        results = []
        for r in data['docs']:
            links = r['pnx'].get('links',False)
            if links:
                avail_links = []
                for link in links:
                    avail_links.append(link)

            titles = []
            search_title = r['pnx']['search'].get('title', False)
            display_title = r['pnx']['display'].get('title',False)
            if search_title:
                titles.append(
                    {
                        "search_title": search_title 
                    }
                )
            if display_title:
                titles.append(
                    {
                        "display_title": display_title 
                    }
                )

            descriptions = [
                {"search_description": r['pnx']['search'].get('description', False)},
                {"display_description": r['pnx']['display'].get('description', False)},
                {"abstract": r['pnx']['addata'].get('abstract', False)}
            ]

            results.append(
                {
                    "links": avail_links,
                    "titles": titles,   # Handle missing 'title'
                    "description":descriptions ,  # Handle missing 'description'
                    "createdYear": r['pnx']['search'].get('creationdate', 'Unknown year'),  # Handle missing 'creationdate'
                }
            )

        
        # Print and send the results as a JSON message
        print(results)
        
        # Return the results as a JSON string
        return json.dumps(results)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        await emitter.emit(
            status="error",
            description=f"Request failed: {e}",
            done=False
        )

# Simulated data for testing
if __name__ == "__main__":
    query = "mexican cooking pinas"
    base_url = "https://api-na.hosted.exlibrisgroup.com/primo/v1/search"
    params = {
        "apikey": "l8xx91a2ae3e9fe648beb86725588a243b46",
        "vid": "01KSU_INST:NewUI",
        "tab": "Everything",
        "scope": "MyInst_and_CI",
        "format": "json",
        "q": f"any,contains,{query}",
        "pcAvailability": "false"
    }

    # Create an emitter instance
    emitter = Emitter()

    # Run the async search request
    asyncio.run(search_request(emitter, base_url, params))
