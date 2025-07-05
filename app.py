"""
LinkedIn Ghostwriter for Thought Leaders

A Streamlit app that generates a week-long content plan for LinkedIn thought leaders
using Together.ai API, real-time industry news scraping, and user input analysis.

Features:
- User bio, recent post, and industry input form
- Real-time Google News scraping for industry trends
- Together.ai API integration for content generation
- Week-long content plan output (7 posts)
- Viral-optimized prompting for maximum engagement

Requirements: streamlit, requests, bs4, json, re
Usage: streamlit run app.py
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import quote_plus
import time
from typing import List, Dict, Optional
from together import Together

# Page configuration
st.set_page_config(
    page_title="LinkedIn Ghostwriter for Thought Leaders",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
GOOGLE_NEWS_BASE_URL = "https://news.google.com/rss/search"
DEFAULT_MODEL = "meta-llama/Llama-3-8b-chat-hf"

# Viral content frameworks
VIRAL_FRAMEWORKS = [
    "Storytelling with unexpected twists",
    "Bold predictions with supporting evidence",
    "Behind-the-scenes industry revelations",
    "Personal failure turned into lessons",
    "Contrarian perspectives on trending topics",
    "Data-driven insights with visual appeal",
    "Industry myth-busting with facts"
]

class NewsScraperError(Exception):
    """Custom exception for news scraping errors"""
    pass

class TogetherAPIError(Exception):
    """Custom exception for Together.ai API errors"""
    pass

def scrape_google_news(industry_keyword: str, max_headlines: int = 10) -> List[str]:
    """
    Scrape recent industry news headlines from Google News RSS feed.
    
    Args:
        industry_keyword: The industry/topic to search for
        max_headlines: Maximum number of headlines to return
        
    Returns:
        List of news headlines
        
    Raises:
        NewsScraperError: If scraping fails
    """
    try:
        # Construct Google News RSS URL
        search_query = f"{industry_keyword} industry news"
        encoded_query = quote_plus(search_query)
        url = f"{GOOGLE_NEWS_BASE_URL}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse RSS feed
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        headlines = []
        for item in items[:max_headlines]:
            title = item.find('title')
            if title and title.text:
                # Clean up title text
                clean_title = re.sub(r'\s+', ' ', title.text.strip())
                headlines.append(clean_title)
        
        return headlines
        
    except requests.RequestException as e:
        raise NewsScraperError(f"Failed to fetch news: {str(e)}")
    except Exception as e:
        raise NewsScraperError(f"Failed to parse news feed: {str(e)}")

def construct_viral_prompt(bio: str, recent_post: str, industry: str, headlines: List[str]) -> str:
    """
    Construct an enhanced, viral-optimized prompt for Together.ai API.
    
    Args:
        bio: User's LinkedIn bio
        recent_post: User's recent LinkedIn post
        industry: User's industry
        headlines: List of current industry news headlines
        
    Returns:
        Formatted prompt string optimized for viral content
    """
    headlines_text = "\n".join([f"• {headline}" for headline in headlines])
    
    prompt = f"""You are an elite LinkedIn ghostwriter and viral content strategist with expertise in creating thought leadership content that achieves maximum engagement, shares, and industry influence. Your mission is to craft a strategic 7-day content calendar that positions the user as an authoritative voice while driving exceptional viral performance.

TARGET PROFILE ANALYSIS:
Industry: {industry}
Professional Bio: {bio}
Voice Reference (Recent Post): {recent_post}

CURRENT MARKET INTELLIGENCE:
{headlines_text}

VIRAL CONTENT STRATEGY REQUIREMENTS:

🎯 ENGAGEMENT OPTIMIZATION:
- Each post must include a compelling hook within the first 2 lines
- Use psychological triggers: curiosity gaps, social proof, controversy, urgency
- Incorporate pattern interrupts and unexpected insights
- Design posts for maximum shareability and comment generation

📊 CONTENT PERFORMANCE FRAMEWORK:
- Post length: 150-300 words (optimized for LinkedIn algorithm)
- Include 3-5 strategic hashtags (mix of trending and niche)
- End with strong call-to-action that encourages engagement
- Use formatting that enhances readability (line breaks, emojis, bullets)

🔥 VIRAL CONTENT TYPES (Use variety across 7 days):
1. **Controversial Take**: Challenge conventional industry wisdom
2. **Behind-the-Scenes**: Share exclusive insider perspectives
3. **Prediction Post**: Make bold, data-backed future predictions
4. **Failure Story**: Transform personal setbacks into teachable moments
5. **Industry Myth-Buster**: Debunk common misconceptions with evidence
6. **Trend Analysis**: Connect current events to industry implications
7. **Contrarian Insight**: Present unpopular but valuable perspectives

💡 PSYCHOLOGICAL ENGAGEMENT TACTICS:
- Open loops and curiosity gaps
- Social proof and authority positioning
- Emotional storytelling with logical conclusions
- Surprise elements and unexpected twists
- Interactive elements encouraging responses

🎨 CONTENT ARCHITECTURE:
- Hook (attention-grabbing opening)
- Context (relevant background/story)
- Core insight (valuable takeaway)
- Evidence (data, examples, proof points)
- Call-to-action (engagement driver)

VOICE MATCHING PROTOCOL:
Analyze the provided recent post and bio to maintain consistent:
- Tone and personality
- Industry expertise level
- Communication style
- Professional positioning
- Authentic voice patterns

FORMAT REQUIREMENTS:
**Day 1: [Compelling Title with Emotional Hook]**
[Post content with strategic formatting]
[3-5 relevant hashtags]
[Strong call-to-action]

**Day 2: [Next Compelling Title]**
[Post content with strategic formatting]
[3-5 relevant hashtags]
[Strong call-to-action]

[Continue for all 7 days]

VIRAL SUCCESS METRICS TO OPTIMIZE FOR:
- Comments: Design posts that naturally generate discussion
- Shares: Create content worth sharing with networks
- Saves: Provide actionable insights people want to reference
- Profile visits: Position expertise to drive connection requests
- Industry influence: Establish thought leadership authority

EXECUTION STANDARDS:
- Every post must provide genuine value to the reader
- Maintain professional credibility while being engaging
- Ensure content is original and not recycled industry clichés
- Balance personal authenticity with strategic viral elements
- Create content that reflects expertise while being accessible

Generate 7 strategically different posts that collectively build a powerful thought leadership narrative while maximizing viral potential across diverse content formats and engagement strategies."""

    return prompt

def call_together_api(prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    """
    Call Together.ai API using the official Python SDK.
    
    Args:
        prompt: The prompt to send to the API
        api_key: Together.ai API key
        model: Model to use for generation
        
    Returns:
        Generated content from the API
        
    Raises:
        TogetherAPIError: If API call fails
    """
    try:
        # Initialize Together client
        client = Together(api_key=api_key)
        
        # Create chat completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=3000,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.1,
            stop=["<|im_end|>", "<|endoftext|>"]
        )
        
        # Extract the generated content
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            raise TogetherAPIError("No content generated by API")
        
    except Exception as e:
        raise TogetherAPIError(f"API request failed: {str(e)}")

def parse_generated_content(content: str) -> Dict[str, str]:
    """
    Parse the generated content into individual daily posts.
    
    Args:
        content: Raw generated content from API
        
    Returns:
        Dictionary mapping day numbers to post content
    """
    posts = {}
    
    # Split content by day markers
    day_pattern = r'\*\*Day (\d+):[^*]*\*\*'
    day_matches = list(re.finditer(day_pattern, content, re.IGNORECASE))
    
    for i, match in enumerate(day_matches):
        day_num = match.group(1)
        start_pos = match.end()
        
        # Find the end position (start of next day or end of content)
        if i + 1 < len(day_matches):
            end_pos = day_matches[i + 1].start()
        else:
            end_pos = len(content)
        
        # Extract post content
        post_content = content[start_pos:end_pos].strip()
        
        # Clean up the content
        post_content = re.sub(r'^\n+', '', post_content)
        post_content = re.sub(r'\n+$', '', post_content)
        
        posts[day_num] = post_content
    
    return posts

def display_sidebar():
    """Display the sidebar with app information and viral content tips."""
    st.sidebar.title("🚀 LinkedIn Ghostwriter Pro")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("🎯 Viral Content Strategy:")
    st.sidebar.markdown("""
    1. **Profile Analysis**: Bio + recent post voice matching
    2. **Industry Intelligence**: Real-time news integration
    3. **Viral Framework**: 7 strategic content types
    4. **Engagement Optimization**: Psychological triggers included
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔥 Viral Content Types:")
    st.sidebar.markdown("""
    - **Controversial Takes**: Challenge industry norms
    - **Behind-the-Scenes**: Exclusive insights
    - **Bold Predictions**: Data-backed forecasts
    - **Failure Stories**: Vulnerability + lessons
    - **Myth-Busting**: Debunk misconceptions
    - **Trend Analysis**: Connect news to insights
    - **Contrarian Views**: Unpopular but valuable
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 Engagement Maximizers:")
    st.sidebar.markdown("""
    - Strong hooks in first 2 lines
    - Curiosity gaps and open loops
    - Interactive call-to-actions
    - Strategic hashtag placement
    - Emotional storytelling
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Get Together.ai API Key:")
    st.sidebar.markdown("""[Sign up at Together.ai](https://together.ai)
    
✨ **Free Credits Available!**
New users get free credits to try the service.""")

def main():
    """Main application function."""
    
    # Display sidebar
    display_sidebar()
    
    # Main header
    st.title("🚀 LinkedIn Ghostwriter for Thought Leaders")
    st.markdown("**Generate viral-optimized content that drives engagement, shares, and industry influence**")
    st.markdown("---")
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Viral Frameworks", "7 Types", "Engagement Optimized")
    with col2:
        st.metric("📊 Content Strategy", "Psychology-Based", "Algorithm Friendly")
    with col3:
        st.metric("🔥 Success Rate", "High Engagement", "Thought Leadership")
    
    st.markdown("---")
    
    # Input form
    with st.form("viral_content_generator"):
        st.subheader("📋 Professional Profile Input")
        
        # User inputs
        col1, col2 = st.columns(2)
        
        with col1:
            bio = st.text_area(
                "🎯 LinkedIn Bio / Professional Summary",
                placeholder="Enter your complete LinkedIn bio or professional summary that showcases your expertise, background, and unique value proposition...",
                help="The more comprehensive your bio, the better the AI can match your professional voice and positioning",
                height=150
            )
            
            industry = st.text_input(
                "🏢 Industry/Niche Keyword",
                placeholder="e.g., fintech, healthcare AI, B2B SaaS, digital marketing",
                help="Be specific - this drives our real-time news scraping and trend analysis"
            )
        
        with col2:
            recent_post = st.text_area(
                "📝 Recent High-Performing Post",
                placeholder="Paste your most recent LinkedIn post that represents your authentic voice, style, and the type of engagement you want to replicate...",
                help="This is crucial for voice matching - choose a post that performed well and represents your style",
                height=150
            )
            
            api_key = st.text_input(
                "🔑 Together.ai API Key",
                type="password",
                placeholder="Enter your Together.ai API key",
                help="Required for AI-powered content generation. Get yours at together.ai - they offer free credits!"
            )
        
        # Advanced settings
        with st.expander("⚙️ Advanced Viral Optimization Settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                model = st.selectbox(
                    "🤖 AI Model Selection",
                    options=[
                        "meta-llama/Llama-3-8b-chat-hf",
                        "meta-llama/Llama-3-70b-chat-hf",
                        "meta-llama/Llama-2-70b-chat-hf",
                        "meta-llama/Llama-2-13b-chat-hf",
                        "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "mistralai/Mistral-7B-Instruct-v0.1"
                    ],
                    help="Llama-3 models generally produce the highest quality content. Larger models are more capable but slower."
                )
                
                max_headlines = st.slider(
                    "📰 Industry News Headlines",
                    min_value=5,
                    max_value=20,
                    value=12,
                    help="More headlines = better trend integration, but may slow generation"
                )
            
            with col2:
                content_focus = st.multiselect(
                    "🎯 Content Focus Areas",
                    options=[
                        "Leadership insights",
                        "Industry predictions",
                        "Personal stories",
                        "Contrarian takes",
                        "Behind-the-scenes",
                        "Data-driven analysis",
                        "Future trends"
                    ],
                    default=["Leadership insights", "Industry predictions", "Personal stories"],
                    help="Select focus areas for your content mix"
                )
                
                engagement_style = st.selectbox(
                    "💬 Engagement Style",
                    options=[
                        "Professional + Engaging",
                        "Bold + Thought-Provoking",
                        "Authentic + Vulnerable",
                        "Data-Driven + Analytical"
                    ],
                    help="Choose the overall tone for maximum engagement"
                )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Generate Viral Content Strategy", use_container_width=True)
    
    # Process form submission
    if submitted:
        # Validate inputs
        if not all([bio, recent_post, industry, api_key]):
            st.error("⚠️ Please fill in all required fields to generate your viral content strategy.")
            return
        
        try:
            # Show progress with enhanced messaging
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Scrape news
            status_text.text("📰 Analyzing real-time industry trends and news...")
            progress_bar.progress(20)
            
            headlines = scrape_google_news(industry, max_headlines)
            
            if not headlines:
                st.warning("⚠️ Limited recent news found. Proceeding with general industry content generation.")
                headlines = [
                    f"Latest innovations in {industry}",
                    f"Market trends shaping {industry}",
                    f"Leadership challenges in {industry}"
                ]
            
            # Step 2: Construct viral prompt
            status_text.text("🧠 Constructing viral-optimized AI prompt strategy...")
            progress_bar.progress(40)
            
            prompt = construct_viral_prompt(bio, recent_post, industry, headlines)
            
            # Step 3: Generate content
            status_text.text("✨ Generating your viral content strategy (this may take 30-45 seconds)...")
            progress_bar.progress(70)
            
            generated_content = call_together_api(prompt, api_key, model)
            
            # Step 4: Parse and display results
            status_text.text("📝 Optimizing and formatting your viral posts...")
            progress_bar.progress(90)
            
            posts = parse_generated_content(generated_content)
            
            # Final step
            status_text.text("🎉 Your viral content strategy is ready!")
            progress_bar.progress(100)
            
            time.sleep(0.5)  # Brief pause for effect
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results with enhanced styling
            st.success("🎉 **Your Viral Content Strategy is Ready!**")
            st.balloons()
            
            # Results summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Posts Generated", len(posts), "Strategic Mix")
            with col2:
                st.metric("📰 Trends Analyzed", len(headlines), "Real-time")
            with col3:
                st.metric("🎯 Viral Elements", "Multiple", "Engagement Optimized")
            
            st.markdown("---")
            
            # Show scraped headlines
            with st.expander("📰 Industry Intelligence Used in Your Content"):
                st.write("**Recent headlines integrated into your strategy:**")
                for i, headline in enumerate(headlines, 1):
                    st.write(f"{i}. {headline}")
            
            st.markdown("---")
            
            # Display generated posts with enhanced formatting
            st.subheader("📅 Your 7-Day Viral Content Calendar")
            st.markdown("*Each post is strategically designed for maximum engagement and shareability*")
            
            if posts:
                # Create tabs for better organization
                tab_names = [f"Day {i}" for i in range(1, min(8, len(posts) + 1))]
                tabs = st.tabs(tab_names)
                
                for i, (day_num, tab) in enumerate(zip(sorted(posts.keys(), key=int), tabs)):
                    with tab:
                        st.markdown(f"### Day {day_num} Content")
                        
                        # Display post content
                        st.markdown("**Preview:**")
                        st.markdown(posts[day_num])
                        
                        # Copy functionality
                        st.markdown("**Copy for LinkedIn:**")
                        st.code(posts[day_num], language=None)
                        
                        # Engagement tips
                        st.markdown("**💡 Posting Tips:**")
                        st.markdown("""
                        - Post during peak hours (8-10 AM, 12-2 PM, 5-6 PM)
                        - Engage with comments within first 2 hours
                        - Share in relevant LinkedIn groups
                        - Tag relevant industry connections
                        """)
                        
                        st.markdown("---")
                
                # Additional strategic advice
                st.markdown("---")
                st.subheader("🎯 Viral Content Execution Strategy")
                
                advice_col1, advice_col2 = st.columns(2)
                
                with advice_col1:
                    st.markdown("**📈 Maximize Engagement:**")
                    st.markdown("""
                    - Respond to comments within 2 hours
                    - Ask follow-up questions in comments
                    - Share insights in your network
                    - Cross-promote on other platforms
                    - Tag relevant industry leaders
                    """)
                
                with advice_col2:
                    st.markdown("**🔄 Content Amplification:**")
                    st.markdown("""
                    - Repurpose top performers into articles
                    - Create carousel posts from insights
                    - Share behind-the-scenes content
                    - Engage with your network's content
                    - Join relevant industry conversations
                    """)
                
            else:
                st.warning("⚠️ Could not parse the generated content properly. Here's the raw output:")
                st.text_area("Raw Generated Content", generated_content, height=500)
                
        except NewsScraperError as e:
            st.error(f"📰 News scraping encountered an issue: {str(e)}")
            st.info("💡 Don't worry - we can still generate excellent content based on your profile and industry knowledge.")
            
        except TogetherAPIError as e:
            st.error(f"🤖 Content generation failed: {str(e)}")
            st.info("💡 Please verify your API key and ensure you have sufficient credits. Together.ai offers free credits when you sign up at together.ai")
            
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred: {str(e)}")
            st.info("💡 Please try again or contact support if the issue persists.")

if __name__ == "__main__":
    main()
