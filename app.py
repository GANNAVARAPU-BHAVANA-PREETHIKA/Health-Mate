import streamlit as st
import os
from utils.search import google_custom_search, prioritize_authoritative_sources
from utils.web_scraping import extract_text_from_url, filter_relevant_context
from utils.llm import generate_response_with_llm
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env

# Set page configuration
st.set_page_config(
    page_title="Ask Dr.AI",
    page_icon="🩺",
    layout="wide",
)

# Main title and description
st.title("🏥 Ask Dr.AI")
st.markdown("""
This AI-powered healthcare assistant provides information about drugs (uses, side effects, precautions) 
and explains medical terms in simple language. The information is sourced from authoritative 
medical websites and explained using advanced AI language models.
""")



# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar with options
with st.sidebar:
    st.header("Dr.AI Options")
    query_type = st.radio(
        "I want to search for a:",
        ["Drug", "Medical Term"],
        index=0
    )
    
    # LLM model selection
    llm_model = st.selectbox(
        "LLM Model",
        ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        index=0
    )
    
    # About section
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This app uses:
    - Retrieval Augmented Generation (RAG)
    - LLM for information synthesis
    - Google Custom Search for authoritative sources
    """)

# Main chat interface
st.markdown("## 💬 Chat")

# Input area
with st.form(key="query_form", clear_on_submit=True):
    user_input = st.text_input(
        f"Enter the name of a {query_type.lower()}:",
        placeholder=f"E.g., {'Aspirin' if query_type == 'Drug' else 'Hypertension'}",
    )
    submit_button = st.form_submit_button("Search")

# Process the query when submitted
if submit_button and user_input:
    # Show spinner while processing
    with st.spinner(f"Searching for information about {user_input}..."):
        try:
            # Add user query to chat history
            st.session_state.chat_history.append({"role": "user", "content": f"Tell me about the {query_type.lower()} {user_input}"})
            
            # Construct search query based on query type
            if query_type == "Drug":
                search_query = f"site:gov OR site:edu OR site:org {user_input} uses side effects precautions drug medication"
                question = f"What are the uses, side effects, and precautions for the drug {user_input}? Explain in simple terms."
            else:
                search_query = f"site:gov OR site:edu OR site:org {user_input} definition causes symptoms treatment medical condition"
                question = f"What is {user_input} in medical terms? Explain the causes, symptoms, and treatments in simple language that a non-medical person can understand."
            
            # Get search results using environment variables
            search_results = google_custom_search(
                search_query, 
                os.getenv("API_KEY_GOOGLE"), 
                os.getenv("CSE_ID")
            )
            
            if not search_results:
                raise Exception("No search results found. Please try another query.")
            
            # Prioritize sources and extract text
            prioritized_urls = prioritize_authoritative_sources(search_results)
            
            # Progress bar for scraping
            progress_bar = st.progress(0)
            combined_context = ""
            
            # Debug information in sidebar
            with st.sidebar:
                with st.expander("Debug Information", expanded=False):
                    st.write("URLs being scraped:")
                    for url in prioritized_urls[:5]:
                        st.write(f"- {url}")
            
            urls_fetched = 0
            for i, url in enumerate(prioritized_urls[:5]):  # Limit to first 5 to avoid taking too long
                content = extract_text_from_url(url)
                if content and len(content.strip()) > 100 and "No content found" not in content and "Could not retrieve content" not in content:
                    combined_context += content + " "
                    urls_fetched += 1
                progress_bar.progress((i + 1) / min(5, len(prioritized_urls)))
            
            progress_bar.empty()
            
            if not combined_context.strip():
                if urls_fetched == 0:
                    raise Exception("Could not extract content from any of the search results. Please try another query or check your internet connection.")
                else:
                    raise Exception("Could not extract relevant text from search results. Please try another query.")
            
            # Filter context to relevant information
            filtered_context = filter_relevant_context(combined_context, user_input)
            
            # Generate response using LLM with environment variable
            response = generate_response_with_llm(filtered_context, question, os.getenv("API_KEY_GROQ"), llm_model)
            
            # Add response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            st.error(error_message)
            st.session_state.chat_history.append({"role": "assistant", "content": error_message})

# Display chat history
st.markdown("### Conversation History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")
    st.markdown("---")

# Clear chat history button
if st.session_state.chat_history:
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
