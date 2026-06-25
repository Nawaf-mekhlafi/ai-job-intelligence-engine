import streamlit as st
import plotly.graph_objects as go
import sys
import os
from io import BytesIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.document_parser import DocumentParser
from utils.docx_generator import DocumentGenerator
from ai_engine.ai_agent import JobMatchAgent

st.set_page_config(
    page_title="JobFit AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_aurora_glassmorphism():
    """
    Injects the Enterprise Aurora Glassmorphism UI and hides all Streamlit default elements.
    """
    imports = """
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    """
    
    css_rules = """
    /* Clean UI: Hide all Streamlit clutter */
    [data-testid="stToolbar"], header, footer, #MainMenu, .stDeployButton {display: none !important; visibility: hidden !important;}
    a.header-anchor {display: none !important;}
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    
    .stApp { 
        background-color: #030712 !important; 
        background-image: radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.12) 0px, transparent 50%) !important; 
        color: #F8FAFC !important; 
        background-attachment: fixed !important;
    }
    
    h1, h2, h3, h4, p, span, label, li { font-family: 'Plus Jakarta Sans', sans-serif !important; color: #F8FAFC !important; }
    
    /* Glassmorphism Cards & Inputs */
    div[data-testid="stFileUploader"], div[data-testid="stTextArea"], .glass-card { 
        background: rgba(17, 24, 39, 0.55) !important; 
        backdrop-filter: blur(24px) !important; 
        border: 1px solid rgba(255, 255, 255, 0.08) !important; 
        border-radius: 16px !important; 
        padding: 1.5rem !important; 
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important; 
        margin-bottom: 1rem;
    }
    
    /* Fix for invisible text in file uploader */
    [data-testid="stFileUploadDropzone"] div { color: #94A3B8 !important; }
    [data-testid="stFileUploadDropzone"] small { color: #64748B !important; }
    [data-testid="stFileUploadDropzone"] button { color: #F8FAFC !important; border: 1px solid rgba(255,255,255,0.2) !important; background: rgba(255,255,255,0.05) !important; }
    
    /* Fix for text area input */
    .stTextArea > div > div > textarea { background-color: transparent !important; border: none !important; color: #F8FAFC !important; }
    .stTextArea > div > div > textarea::placeholder { color: #64748B !important; opacity: 1 !important; }
    
    /* Premium Buttons */
    div[data-testid="stButton"] > button { 
        width: 100%; 
        background: linear-gradient(135deg, #4F46E5, #9333EA) !important; 
        color: #FFFFFF !important; 
        border: none !important; 
        border-radius: 12px !important; 
        font-weight: 700 !important; 
        padding: 1rem 0 !important; 
        box-shadow: 0 4px 15px rgba(147, 51, 234, 0.25) !important; 
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(147, 51, 234, 0.4) !important; }
    
    div[data-testid="stDownloadButton"] > button { background: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #F8FAFC !important; }
    .fa-fw { margin-right: 8px; color: #A855F7; }
    </style>
    """
    st.markdown(imports + css_rules.replace('\n', ''), unsafe_allow_html=True)

def render_gauge_chart(score: int):
    """Renders the semantic match score gauge chart."""
    if score <= 30: bar_color = "#EF4444"
    elif score <= 70: bar_color = "#F59E0B"
    else: bar_color = "#10B981"

    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        number = {'font': {'size': 42, 'color': '#F8FAFC'}, 'suffix': "%"},
        gauge = {'axis': {'visible': False, 'range': [0, 100]}, 'bar': {'color': bar_color, 'thickness': 0.75}, 'bgcolor': "rgba(30, 41, 59, 0.4)", 'borderwidth': 0}
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=250, margin=dict(l=10, r=10, t=10, b=10))
    return fig

def main():
    inject_aurora_glassmorphism()
    
    if 'analysis_results' not in st.session_state: 
        st.session_state.analysis_results = None
    
    st.markdown("<br><br><h1><i class='fa-solid fa-bolt fa-fw'></i> JobFit AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.1rem;'>Smart CV Analysis & ATS Optimization System</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("<h3><i class='fa-solid fa-file-pdf fa-fw'></i> 1. Candidate Profile</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Professional CV (PDF)", type=["pdf"])
    with col2:
        st.markdown("<h3><i class='fa-solid fa-clipboard-list fa-fw'></i> 2. Target Role</h3>", unsafe_allow_html=True)
        job_input = st.text_area("Paste Raw Job Description", height=130, placeholder="Copy and paste the full job description text here...")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Initialize Semantic Analysis"):
        if uploaded_file and job_input:
            if "http://" in job_input.lower() or "https://" in job_input.lower() or "www." in job_input.lower():
                st.error("🚫 **URL Detected:** To ensure 100% accuracy and avoid website security blocks, please copy and paste the **RAW TEXT** of the job description instead of a link.")
            else:
                with st.spinner("Executing Strict AI Inference..."):
                    try:
                        cv_text = DocumentParser.extract_text_from_pdf(BytesIO(uploaded_file.getvalue()))
                        agent = JobMatchAgent()
                        st.session_state.analysis_results = agent.analyze_cv_against_job(cv_text, job_input)
                    except Exception as e:
                        st.error(f"Execution Error: {str(e)}")
        else: 
            st.warning("Please provide both a CV and a Job Description.")

    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("<h2><i class='fa-solid fa-chart-pie fa-fw'></i> Diagnostic Results</h2>", unsafe_allow_html=True)
        
        # 1. Score & Summary
        c1, c2 = st.columns([1, 1.5], gap="large")
        with c1: 
            st.markdown("<div style='text-align: center; color: #94A3B8; font-weight: 600;'>Semantic Match Score</div>", unsafe_allow_html=True)
            st.plotly_chart(render_gauge_chart(res.get('match_score', 0)), use_container_width=True, config={'displayModeBar': False})
        with c2: 
            st.markdown("<h4><i class='fa-solid fa-microchip fa-fw'></i> Overall Fit Summary</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='glass-card' style='line-height: 1.6;'>{res.get('overall_summary', 'N/A')}</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        # 2. Keywords
        k1, k2 = st.columns(2, gap="large")
        with k1:
            st.markdown("<h4><i class='fa-solid fa-check-double fa-fw' style='color:#10B981;'></i> Verified Skills</h4>", unsafe_allow_html=True)
            match_html = "".join([f"<span style='display:inline-block; background:rgba(16, 185, 129, 0.15); color:#34D399; padding:6px 14px; border-radius:20px; margin:4px; border:1px solid rgba(16, 185, 129, 0.4); font-size:0.9em; font-weight:500;'>{k}</span>" for k in res.get('matching_keywords', [])])
            st.markdown(f"<div class='glass-card'>{match_html or 'No matches found.'}</div>", unsafe_allow_html=True)
        with k2:
            st.markdown("<h4><i class='fa-solid fa-triangle-exclamation fa-fw' style='color:#F43F5E;'></i> Identified Gaps</h4>", unsafe_allow_html=True)
            missing_html = "".join([f"<span style='display:inline-block; background:rgba(244, 63, 94, 0.15); color:#FB7185; padding:6px 14px; border-radius:20px; margin:4px; border:1px solid rgba(244, 63, 94, 0.4); font-size:0.9em; font-weight:500;'>{k.get('skill', str(k)) if isinstance(k, dict) else str(k)}</span>" for k in res.get('missing_keywords', [])])
            st.markdown(f"<div class='glass-card'>{missing_html or 'No critical gaps.'}</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 3. CV Improvements
        g1, g2 = st.columns(2, gap="large")
        with g1:
            st.markdown("<h4><i class='fa-solid fa-shield-halved fa-fw'></i> ATS CV Improvements</h4>", unsafe_allow_html=True)
            ats_html = "".join([f"<li style='margin-bottom: 12px; color: #E2E8F0;'>{item}</li>" for item in res.get('ats_improvements', [])])
            st.markdown(f"<div class='glass-card'><ul style='padding-left: 20px;'>{ats_html}</ul></div>", unsafe_allow_html=True)
        with g2:
            st.markdown("<h4><i class='fa-solid fa-pen-nib fa-fw'></i> Suggested Bullet Improvements</h4>", unsafe_allow_html=True)
            bull_html = "".join([f"<li style='margin-bottom: 12px; color: #E2E8F0;'>{item}</li>" for item in res.get('bullet_improvements', [])])
            st.markdown(f"<div class='glass-card'><ul style='padding-left: 20px;'>{bull_html}</ul></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Educational Router & Reverse Jobs
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.markdown("<h4><i class='fa-solid fa-map-location-dot fa-fw'></i> Smart Educational Router</h4>", unsafe_allow_html=True)
            router_html = ""
            for missing in res.get('missing_keywords', []):
                skill = missing.get('skill', str(missing)) if isinstance(missing, dict) else str(missing)
                platform = missing.get('platform', 'Coursera / Udemy') if isinstance(missing, dict) else 'Coursera / Udemy'
                router_html += f"<div style='background: rgba(255,255,255,0.03); padding: 12px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #A855F7;'><strong style='color:#F8FAFC;'>{skill}</strong><br><span style='color: #94A3B8; font-size: 0.85em;'><i class='fa-solid fa-graduation-cap'></i> Recommended Platform: <span style='color:#A855F7;'>{platform}</span></span></div>"
            st.markdown(f"<div class='glass-card'>{router_html or 'Analysis pending...'}</div>", unsafe_allow_html=True)
        with r2:
            st.markdown("<h4><i class='fa-solid fa-briefcase fa-fw'></i> Recommended Job Titles</h4>", unsafe_allow_html=True)
            rev_html = "".join([f"<li style='margin-bottom: 12px; color: #E2E8F0;'><strong>{item}</strong></li>" for item in res.get('reverse_job_recommendations', [])])
            st.markdown(f"<div class='glass-card'><ul style='padding-left: 20px;'>{rev_html}</ul></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. Cover Letter (Robust formatting using white-space: pre-wrap)
        st.markdown("<h3><i class='fa-solid fa-envelope-open-text fa-fw'></i> Enterprise Cover Letter</h3>", unsafe_allow_html=True)
        raw_letter = res.get('cover_letter_draft', '')
        
        # Using white-space: pre-wrap guarantees that any \n returned by the LLM is respected perfectly by the browser
        st.markdown(f"<div class='glass-card' style='line-height: 1.8; font-size: 1.05rem; color: #E2E8F0; padding: 2rem; white-space: pre-wrap;'>{raw_letter}</div>", unsafe_allow_html=True)
        
        st.download_button(
            label="📥 Download as Word Document",
            data=DocumentGenerator.create_cover_letter_docx(raw_letter),
            file_name="Enterprise_Cover_Letter.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

if __name__ == "__main__": 
    main()