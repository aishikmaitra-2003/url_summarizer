import streamlit as st
import validators
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import UnstructuredURLLoader
import yt_dlp

load_dotenv()

# Streamlit Config
st.set_page_config(page_title="LangChain Summarizer for Urls:", page_icon="❤️")
st.title("Langchain Url Summarizer")
st.subheader("Project here")

# Groq API Key
groq_api_key = os.getenv("GROQ_KEY")
llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=groq_api_key)

prompt_template = """
Provide a summary of the following content in 500 words:
content: {text}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])



def load_webpage_content(url: str) -> list[Document]:
    """Scrape webpage content using requests + BeautifulSoup."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=15, verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove junk tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Try to find the main article content
    content = ""
    for selector in ["article", "main", '[class*="article"]', '[class*="content"]', '[class*="story"]']:
        block = soup.select_one(selector)
        if block:
            content = block.get_text(separator=" ", strip=True)
            break

    # Fallback to full body text
    if not content or len(content) < 200:
        content = soup.body.get_text(separator=" ", strip=True) if soup.body else ""

    if not content.strip():
        raise ValueError("Could not extract any content from the webpage.")

    title = soup.title.string if soup.title else url

    return [Document(page_content=content, metadata={"source": url, "title": title})]


def load_youtube_transcript(url: str) -> list[Document]:
    """Extract YouTube transcript/subtitles using yt-dlp."""
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title = info.get("title", "Unknown Title")
    description = info.get("description", "")
    uploader = info.get("uploader", "Unknown")
    duration = info.get("duration", 0)

    # Try to get subtitles text if available
    subtitles = info.get("subtitles", {})
    auto_subs = info.get("automatic_captions", {})
    transcript_text = ""

    # Prefer manual subtitles, fallback to auto-captions
    sub_source = subtitles if subtitles else auto_subs
    if sub_source:
        lang = next(iter(sub_source))  # pick first available language
        entries = sub_source[lang]
        # entries is a list of format dicts; find json3 or ttml for text
        for fmt in entries:
            if fmt.get("ext") == "json3":
                import urllib.request, json
                with urllib.request.urlopen(fmt["url"]) as r:
                    raw = json.loads(r.read())
                events = raw.get("events", [])
                transcript_text = " ".join(
                    seg.get("utf8", "")
                    for e in events
                    for seg in e.get("segs", [])
                ).strip()
                break

    # Build content from whatever we have
    content_parts = [f"Title: {title}", f"Uploader: {uploader}", f"Duration: {duration}s"]
    if transcript_text:
        content_parts.append(f"\nTranscript:\n{transcript_text}")
    elif description:
        content_parts.append(f"\nDescription:\n{description}")
    else:
        raise ValueError("No transcript or description found for this video.")

    return [Document(page_content="\n".join(content_parts), metadata={"source": url, "title": title})]


generic_url = st.text_input("Enter the URL here:", label_visibility="collapsed")

# if st.button("Summarize"):
#     if not groq_api_key.strip() or not generic_url.strip():
#         st.error("Please enter a URL")
#     elif not validators.url(generic_url):
#         st.error("Please enter a valid URL")
#     else:
#         try:
#             with st.spinner("Loading...."):
#                 if "youtube.com" in generic_url or "youtu.be" in generic_url:
#                     data = load_youtube_transcript(generic_url)
#                 else:
#                     loader = UnstructuredURLLoader(
#                         urls=[generic_url],
#                         ssl_verify=False,
#                         headers={
#                             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                                           "AppleWebKit/537.36 (KHTML, like Gecko) "
#                                           "Chrome/91.0.4472.124 Safari/537.36"
#                         },
#                     )
#                     data = loader.load()

#                 chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
#                 output = chain.run(data)
#                 st.success(output)

        # except Exception as e:
        #     st.exception(f"The exception is {e}")
if st.button("Summarize"):
    if not groq_api_key.strip() or not generic_url.strip():
        st.error("Please enter a URL")
    elif not validators.url(generic_url):
        st.error("Please enter a valid URL")
    else:
        try:
            with st.spinner("Loading...."):
                if "youtube.com" in generic_url or "youtu.be" in generic_url:
                    data = load_youtube_transcript(generic_url)
                else:
                    data = load_webpage_content(generic_url)  # ← replaced

                chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
                output = chain.run(data)
                st.success(output)

        except Exception as e:
            st.exception(f"The exception is {e}")