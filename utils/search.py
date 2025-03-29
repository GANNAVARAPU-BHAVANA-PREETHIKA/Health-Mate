import requests

def google_custom_search(query, api_key, cse_id, num_results=10):
    """
    Performs a Google Custom Search for a given query.
    
    Args:
        query (str): The search query
        api_key (str): Google API key
        cse_id (str): Google Custom Search Engine ID
        num_results (int): Number of results to return
        
    Returns:
        list: A list of URLs from the search results
    """
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "num": num_results,
    }
    try:
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        response.raise_for_status()
        results = response.json().get("items", [])
        return [item["link"] for item in results]
    except Exception as e:
        print(f"Error with Google API: {e}")
        return []

def prioritize_authoritative_sources(urls):
    """
    Sorts URLs to prioritize authoritative medical domains.
    
    Args:
        urls (list): List of URLs to prioritize
        
    Returns:
        list: Sorted list of URLs with authoritative sources first
    """
    # List of authoritative domains in order of priority
    authoritative_domains = [
        ".gov", 
        ".edu", 
        ".org", 
        "mayoclinic.org", 
        "webmd.com", 
        "nih.gov", 
        "medlineplus.gov",
        "cdc.gov",
        "fda.gov",
        "who.int"
    ]
    
    # Score function: higher if URL has a more authoritative domain
    def get_authority_score(url):
        for i, domain in enumerate(authoritative_domains):
            if domain in url:
                return len(authoritative_domains) - i
        return 0
    
    # Sort URLs by authority score (highest first)
    return sorted(urls, key=get_authority_score, reverse=True)
