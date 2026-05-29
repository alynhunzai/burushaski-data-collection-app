"""
Streamlit frontend for the NLP data collection app.

This module provides a clean, mobile-friendly interface for users to register,
view source sentences, and submit translations. It communicates with the FastAPI
backend running on localhost:8000.
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any
from uuid import UUID
import os
import json

# Configure Streamlit page
st.set_page_config(
    page_title="Burushaski Language Data Collection",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend API configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
DIALECTS = ["Hunza", "Nagar", "Yasin"]

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "dialect" not in st.session_state:
    st.session_state.dialect = None
if "current_sentence" not in st.session_state:
    st.session_state.current_sentence = None
if "translation_submitted" not in st.session_state:
    st.session_state.translation_submitted = False
if "current_unverified_translation" not in st.session_state:
    st.session_state.current_unverified_translation = None
if "vote_submitted" not in st.session_state:
    st.session_state.vote_submitted = False


def register_user(username: str, dialect: str) -> Optional[Dict[str, Any]]:
    """
    Register a new user with the backend.

    Args:
        username: The username to register
        dialect: The user's dialect (HUNZA, NAGAR, YASIN)

    Returns:
        User data dict if successful, None otherwise
    """
    try:
        response = requests.post(
            f"{API_URL}/users/",
            json={
                "username": f"{username}", 
                "dialect": f"{dialect}"
            },
            timeout=90,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Ensure FastAPI is running on port 8000.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 409:
            st.error("❌ Username already exists. Try a different username.")
        else:
            # Safely try to extract JSON error, fallback if Render sends HTML
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except ValueError:
                error_detail = f"Server Error (Status {response.status_code})"
            
            st.error(f"❌ Registration failed: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None


def fetch_random_sentence() -> Optional[Dict[str, Any]]:
    """
    Fetch a random active source sentence from the backend.

    Returns:
        Sentence data dict if successful, None otherwise
    """
    try:
        response = requests.get(f"{API_URL}/sentences/random", timeout=90)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None
    except requests.exceptions.HTTPError:
        st.error("❌ No active sentences available.")
        return None
    except Exception as e:
        st.error(f"❌ Error fetching sentence: {str(e)}")
        return None


def submit_translation(source_id: UUID, user_id: UUID, translated_text: str) -> bool:
    """
    Submit a translation to the backend.

    Args:
        source_id: The ID of the source sentence
        user_id: The ID of the user submitting
        translated_text: The translated text

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            f"{API_URL}/translations/",
            json={
                "source_id": source_id,
                "user_id": user_id,
                "translated_text": translated_text,
            },
            timeout=90,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return False
    except requests.exceptions.HTTPError:
        st.error(f"❌ Submission failed: {response.json().get('detail', 'Unknown error')}")
        return False
    except Exception as e:
        st.error(f"❌ Error submitting translation: {str(e)}")
        return False


def fetch_unverified_translations() -> Optional[Dict[str, Any]]:
    """
    Fetch a list of unverified translations from the backend.

    Returns:
        List of translation data dicts if successful, None otherwise
    """
    try:
        response = requests.get(f"{API_URL}/translations/unverified", timeout=90)
        response.raise_for_status()
        translations = response.json()
        return translations if translations else None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return None
    except requests.exceptions.HTTPError:
        st.error("❌ Failed to fetch translations.")
        return None
    except Exception as e:
        st.error(f"❌ Error fetching translations: {str(e)}")
        return None


def submit_validation(translation_id: UUID, user_id: UUID, vote: int) -> bool:
    """
    Submit a validation (vote) for a translation.

    Args:
        translation_id: The ID of the translation to validate
        user_id: The ID of the user voting
        vote: The vote value (1 for upvote, -1 for downvote)

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.post(
            f"{API_URL}/validations/",
            json={
                "translation_id": translation_id,
                "user_id": user_id,
                "vote": vote,
            },
            timeout=90,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend.")
        return False
    except requests.exceptions.HTTPError:
        st.error(f"❌ Vote failed: {response.json().get('detail', 'Unknown error')}")
        return False
    except Exception as e:
        st.error(f"❌ Error submitting vote: {str(e)}")
        return False


# Sidebar: User Registration/Login
st.sidebar.title("👤 User Account")

if st.session_state.user_id is None:
    st.sidebar.info("Register to get started!")
    
    with st.sidebar.form("registration_form"):
        username_input = st.text_input(
            "Username",
            placeholder="Enter your username (3-50 chars)",
            max_chars=50,
        )
        dialect_input = st.selectbox(
            "Select Your Dialect",
            DIALECTS,
            help="Choose your native dialect",
        )
        register_button = st.form_submit_button("Register", use_container_width=True)
        
        if register_button:
            if not username_input or len(username_input) < 3:
                st.error("Username must be at least 3 characters long.")
            else:
                user_data = register_user(username_input, dialect_input)
                if user_data:
                    st.session_state.user_id = user_data["id"]
                    st.session_state.username = user_data["username"]
                    st.session_state.dialect = user_data["dialect"]
                    st.success(f"✅ Welcome, {user_data['username']}!")
                    st.rerun()
else:
    st.sidebar.success(f"✅ Logged in as **{st.session_state.username}**")
    st.sidebar.markdown(f"**Dialect:** {st.session_state.dialect}")
    st.sidebar.markdown(f"**User ID:** `{st.session_state.user_id[:8]}...`")
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.dialect = None
        st.session_state.current_sentence = None
        st.rerun()

# Main page
st.title("🌐 Burushaski Corpus Crowdsourcing Platform")

# Welcome message
st.markdown("""Welcome to the Burushaski Corpus Crowdsourcing!\n
This platform is designed to crowdsource a high-quality parallel corpus for Burushaski, 
a low-resource language isolate. Because modern AI models require vast amounts of structured data to learn, 
this app collects community-verified translations of benchmark English sentences into a standardized Latin-based Burushaski orthography. 
Whether you are translating new sentences or validating existing submissions from other native speakers, 
your contributions are crucial to overcoming the linguistic and technical barriers of developing the first robust text-to-text translation models for the Burushaski language.""")

if st.session_state.user_id is None:
    st.info("👈 Please register in the sidebar to get started.")
else:
    st.markdown("---")
    
    # Create two tabs
    tab1, tab2 = st.tabs(["📝 Submit Translation", "✅ Review Translations"])
    
    # Tab 1: Submit Translations
    with tab1:
        # Fetch initial sentence if not already loaded
        if st.session_state.current_sentence is None:
            with st.spinner("Loading sentence..."):
                sentence = fetch_random_sentence()
                if sentence:
                    st.session_state.current_sentence = sentence
        
        if st.session_state.current_sentence:
            sentence_data = st.session_state.current_sentence
            
            # Display the source sentence
            st.subheader("📝 Source Sentence (English)")
            st.info(sentence_data["text"])
            
            # Translation input form
            st.subheader("✍️ Your Translation")
            
            with st.form("translation_form"):
                translation_input = st.text_area(
                    "Translate the sentence above in the standardized Latin script:",
                    placeholder="Enter your translation here...",
                    height=100,
                    label_visibility="collapsed",
                )
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    submit_button = st.form_submit_button("Submit Translation", use_container_width=True)
                with col2:
                    skip_button = st.form_submit_button("Skip This Sentence", use_container_width=True)
                
                if submit_button:
                    if not translation_input or len(translation_input.strip()) == 0:
                        st.error("⚠️ Please enter a translation.")
                    else:
                        with st.spinner("Submitting translation..."):
                            success = submit_translation(
                                sentence_data["id"],
                                st.session_state.user_id,
                                translation_input,
                            )
                            
                            if success:
                                st.session_state.translation_submitted = True
                                st.session_state.current_sentence = None
                                st.success("✅ Translation submitted successfully!")
                                st.balloons()
                                
                                # Auto-load next sentence
                                import time
                                time.sleep(1)
                                st.rerun()
                
                if skip_button:
                    st.session_state.current_sentence = None
                    st.info("⏭️ Skipped. Loading next sentence...")
                    st.rerun()
        else:
            with st.spinner("Loading next sentence..."):
                sentence = fetch_random_sentence()
                if sentence:
                    st.session_state.current_sentence = sentence
                    st.rerun()
                else:
                    st.error("No sentences available at the moment.")
    
    # Tab 2: Review Translations
    with tab2:
        st.subheader("🔍 Community Translation Review")
        st.caption("Review pending translations and vote on their accuracy.")
        
        # Fetch unverified translations if not already loaded
        if st.session_state.current_unverified_translation is None:
            with st.spinner("Loading translation for review..."):
                translations = fetch_unverified_translations()
                if translations and len(translations) > 0:
                    # Find a translation that the user didn't create
                    for translation in translations:
                        if translation["user_id"] != st.session_state.user_id:
                            st.session_state.current_unverified_translation = translation
                            break
                    
                    if st.session_state.current_unverified_translation is None:
                        st.warning("⚠️ All pending translations are yours. You cannot vote on your own translations!")
        
        if st.session_state.current_unverified_translation:
            trans_data = st.session_state.current_unverified_translation
            
            # Display the original sentence
            st.subheader("📝 Original Sentence (English)")
            st.info(f"English sentence: {trans_data['source_sentence']}")
            
            # Fetch the source sentence details (we need to make an endpoint or store it)
            st.info(f"Source ID: {trans_data['source_id']}")
            
            # Display the submitted translation
            st.subheader("✍️ Submitted Translation")
            st.info(trans_data["translated_text"])
            
            # Display vote count
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.metric("Current Votes", trans_data["net_votes"])
            
            st.markdown("---")
            
            # Voting buttons
            st.subheader("🗳️ Cast Your Vote")
            
            col_upvote, col_downvote = st.columns([1, 1], gap="medium")
            
            with col_upvote:
                if st.button("👍 Accurate", use_container_width=True, key="upvote_btn"):
                    with st.spinner("Submitting vote..."):
                        success = submit_validation(
                            trans_data["id"],
                            st.session_state.user_id,
                            1,
                        )
                        
                        if success:
                            st.session_state.current_unverified_translation = None
                            st.session_state.vote_submitted = True
                            st.success("✅ Vote submitted! Loading next translation...")
                            
                            import time
                            time.sleep(1)
                            st.rerun()
            
            with col_downvote:
                if st.button("👎 Incorrect", use_container_width=True, key="downvote_btn"):
                    with st.spinner("Submitting vote..."):
                        success = submit_validation(
                            trans_data["id"],
                            st.session_state.user_id,
                            -1,
                        )
                        
                        if success:
                            st.session_state.current_unverified_translation = None
                            st.session_state.vote_submitted = True
                            st.success("✅ Vote submitted! Loading next translation...")
                            
                            import time
                            time.sleep(1)
                            st.rerun()
        else:
            if st.session_state.current_unverified_translation is None and st.session_state.user_id is not None:
                with st.spinner("Loading next translation..."):
                    translations = fetch_unverified_translations()
                    if translations and len(translations) > 0:
                        # Find a translation that the user didn't create
                        for translation in translations:
                            if translation["user_id"] != st.session_state.user_id:
                                st.session_state.current_unverified_translation = translation
                                st.rerun()
                                break
                        else:
                            st.warning("⚠️ All pending translations are yours or there are no more to review!")
                    else:
                        st.info("✨ Great job! No unverified translations to review at the moment.")

st.markdown("---")
st.caption("NLP Data Collection App | Powered by FastAPI & Streamlit")
