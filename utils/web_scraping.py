import requests
from bs4 import BeautifulSoup
import re

# Try to import trafilatura with error handling
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    print("Trafilatura import failed. Falling back to BeautifulSoup only.")

def extract_text_from_url(url):
    """
    Extracts text content from a URL using BeautifulSoup,
    with trafilatura as a first option if available.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        str: The extracted text content
    """
    try:
        # First try using trafilatura if available
        if TRAFILATURA_AVAILABLE:
            try:
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text and len(text) > 100:  # Check if we got meaningful content
                        return text
            except Exception as e:
                print(f"Trafilatura extraction failed: {e}")
        
        # Fall back to BeautifulSoup
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
            
        # Get text from paragraphs and other text elements
        paragraphs = soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "div.content"])
        text = " ".join([paragraph.get_text() for paragraph in paragraphs])
        
        # Clean the text
        text = " ".join(text.split())
        
        return text if text else "No content found"
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        # Return empty string only if it's a connection error
        # Otherwise return a message that can be displayed to the user
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            return ""
        return f"Could not retrieve content: {str(e)}"

def filter_relevant_context(context, query, top_n=10):
    """
    Filters the most relevant sentences from the context based on keyword matching.
    This is a simplified version that doesn't require sentence-transformers.
    
    Args:
        context (str): The full context text
        query (str): The query to match against
        top_n (int): Number of top sentences to return
        
    Returns:
        str: A filtered context containing only the most relevant sentences
    """
    # Split the context into sentences
    sentences = [s.strip() for s in context.replace('\n', ' ').split('.') if len(s.strip()) > 20]
    
    if not sentences:
        return context
    
    # Create query terms (the query itself and common medical terms)
    query_terms = query.lower().split()
    
    # If the query is a drug, add common terms related to drugs
    drug_related_terms = ["use", "dosage", "indication", "side effect", "adverse", 
                        "warning", "precaution", "interaction", "contraindication", 
                        "mg", "dose", "tablet", "capsule", "injection", "oral"]
    
    # If the query is a medical term, add common explanatory terms
    medical_term_related = ["definition", "cause", "symptom", "treatment", 
                           "diagnose", "condition", "disease", "disorder", 
                           "syndrome", "chronic", "acute"]
    
    # Combine all potential terms
    all_terms = query_terms + drug_related_terms + medical_term_related
    
    # Score sentences based on term frequency
    scored_sentences = []
    for sentence in sentences:
        score = 0
        sentence_lower = sentence.lower()
        
        # Score for exact query match (higher weight)
        if query.lower() in sentence_lower:
            score += 5
        
        # Score for individual terms
        for term in all_terms:
            if term in sentence_lower:
                score += 1
        
        scored_sentences.append((sentence, score))
    
    # Sort sentences by score (highest first)
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # Get the top N sentences
    top_sentences = [sentence for sentence, score in scored_sentences[:top_n] if score > 0]
    
    # If no sentences scored above 0, return a subset of the original context
    if not top_sentences:
        return ". ".join(sentences[:min(top_n, len(sentences))])
    
    # Join the top sentences
    filtered_context = ". ".join(top_sentences)
    
    return filtered_context
