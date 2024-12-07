import streamlit as st
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import os
import openai
from openai import RateLimitError
import time

openai.api_key = os.getenv("OPENAI_API_KEY")
load_dotenv()

loader = CSVLoader(file_path="data.csv")
documents = loader.load()

# Extract text from Document objects
texts = [doc.page_content for doc in documents]


# Function to handle rate limit errors with exponential backoff
def get_embeddings_with_retry(embedding, texts, max_retries=10, initial_wait=1):
    for retry in range(max_retries):
        try:
            return embedding.embed_documents(texts)
        except RateLimitError as e:
            if retry < max_retries - 1:
                wait_time = initial_wait * (2 ** retry)  # Exponential backoff
                st.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                st.error("Rate limit exceeded. Please check your plan and billing details.")
                return None


# Create embeddings with retry logic
embeddings = OpenAIEmbeddings()
embedding_vectors = get_embeddings_with_retry(embeddings, texts)

db = FAISS.from_documents(documents, embeddings)


def retrieve_info(query):
    similar_response = db.similarity_search(query, k=4)
    page_contents_array = [doc.page_content for doc in similar_response]
    return "\n\n".join(page_contents_array)


llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

template = """You are Prasoon Raj himself. Respond naturally as if you are having a direct conversation.

Context about yourself:
{relevant_data}

Question received:
{question}

Guidelines for your responses:
1. You ARE Prasoon - always speak in first person
2. Only share information about yourself that exists in the context data
3. For questions outside your domain or knowledge:
   - Be direct: "I'm not able to comment on that as it's outside my knowledge/experience. However, I'd be happy to discuss my work in AI, data science, or my other professional experiences."
4. For personal questions not in the data:
   - Be honest: "I prefer not to discuss that. Let's focus on my professional background and expertise."
5. For greetings or casual messages:
   - Skip pleasantries and directly ask: "What would you like to know about my work in tech?"
6. For professional questions:
   - Keep responses under 150 words
   - Be specific and reference actual experiences from the context
   - Show enthusiasm for your work while maintaining professionalism
7. Never invent or assume information
8. Don't use phrases like "based on the data" or "according to the information"

Remember: You're Prasoon having a real conversation. Be direct, professional, and only discuss what you actually know from the context. Don't greet back - focus on providing valuable information about your professional experience."""

prompt = PromptTemplate(
    input_variables=["question", "relevant_data"],
    template=template
)

chain = (
        {"question": RunnablePassthrough(), "relevant_data": lambda x: retrieve_info(x["question"])}
        | prompt
        | llm
)


def generate_response(question):
    response = chain.invoke({"question": question})
    return response.content


def main():
    st.set_page_config(
        page_title="Get to know me", page_icon=":male-technologist:")


    st.markdown("""
    <style>
    /* Clean dark theme background */
    .stApp {
        background: #1a1a1a;
    }
    
    /* Minimal styling for content */
    .stMarkdown {
        color: #ffffff;
    }
    
    /* Social icons styling - keeping the hover effects */
    .social-icons {
        text-align: right;
        padding: 10px 0;
    }
    .social-icons a {
        display: inline-block;
        margin-right: 10px;
    }
    .social-icons a:last-child {
        margin-right: 0;
    }
    .social-icons a img {
        width: 30px;
        transition: all 0.3s ease;
        filter: brightness(0.9);
    }
    .social-icons a img:hover {
        transform: translateY(-3px) scale(1.1);
        filter: brightness(1);
    }
    
    /* Clean text styling */
    h1, h3 {
        color: #ffffff !important;
        font-weight: 600;
    }
    p {
        color: #e0e0e0 !important;
    }
    
    /* Subtle button styling */
    .stDownloadButton button {
        background-color: #333333 !important;
        color: white !important;
        border-radius: 5px;
        border: none !important;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stDownloadButton button:hover {
        background-color: #444444 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    /* Clean text area styling */
    .stTextArea textarea {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 5px;
        padding: 10px;
    }
    .stTextArea textarea:focus {
        box-shadow: 0 0 0 2px rgba(77, 77, 77, 0.2);
    }
    
    /* Minimal response container */
    .response-container {
        background-color: #2d2d2d;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Move resume download and social icons to the top
    col4, col5 = st.columns([3, 1])
    with col4:
        with open("resume.pdf", "rb") as file:
            st.download_button(label="Download my Resume", data=file, file_name="Prasoon_Raj_Resume.pdf",
                               mime="application/pdf")
    with col5:
        st.markdown("""
               <div class='social-icons'>
                   <a href='https://www.linkedin.com/in/prasoon-raj-902/' target='_blank' style='margin-right: 10px;'>
                       <img src='https://cdn-icons-png.flaticon.com/512/174/174857.png' width='30'/>
                   </a>
                   <a href='https://github.com/Pra-soon' target='_blank'>
                       <img src='https://cdn-icons-png.flaticon.com/512/733/733553.png' width='30'/>
                   </a>
               </div>
           """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>Get to know me</h1>", unsafe_allow_html=True)

    # Smaller profile picture
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("profile.jpg", width=150, use_column_width=True)

    st.markdown("<h3 style='text-align: center;'>Hi, I'm Prasoon Raj. Feel free to ask me any questions you have!</h3>",
                unsafe_allow_html=True)

    # Add a hint before the text area
    st.markdown("""
        <div style='
            color: #888888;
            font-size: 0.8em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        '>
            <span>💡</span>
            <span>Press Ctrl+Enter to submit your question</span>
        </div>
    """, unsafe_allow_html=True)

    # Text area for input
    message = st.text_area(
        "Your question:",
        height=120,
        label_visibility="collapsed",
        placeholder="Type your question here...",
        key="question_input"
    )

    if message:
        with st.spinner("Thinking... Please wait"):
            result = generate_response(message)
            
        st.markdown(f"""
            <div class='response-container'>
                {result}
            </div>
        """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
