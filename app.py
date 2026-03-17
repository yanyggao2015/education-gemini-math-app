import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="Education Topic Helper",
    page_icon="📘",
    layout="centered"
)

st.title("📘 Education Topic Helper")
st.caption("Generate explanations, key points, quiz questions, and feedback with Gemini.")

# ----------------------------
# API key / client setup
# ----------------------------
api_key = os.getenv("GEMINI_API_KEY")
has_api_key = bool(api_key)

client = genai.Client(api_key=api_key) if has_api_key else None

# ----------------------------
# Sidebar settings
# ----------------------------
st.sidebar.header("Settings")

grade = st.sidebar.selectbox(
    "Student level",
    ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"],
    index=3
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["easy", "medium", "hard"],
    index=1
)

model_name = st.sidebar.selectbox(
    "Model",
    [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-pro-preview"
    ],
    index=0
)

# Optional soft note in sidebar, no error UI
if not has_api_key:
    st.sidebar.caption("Gemini is not connected yet. You can still browse the app interface.")

# ----------------------------
# Main input
# ----------------------------
topic = st.text_input(
    "Enter an education topic",
    value="Grade 11 math: quadratic functions"
)

col1, col2 = st.columns(2)

generate_package = col1.button(
    "Generate Study Package",
    use_container_width=True,
    disabled=not has_api_key
)

generate_quiz = col2.button(
    "Generate Quiz Only",
    use_container_width=True,
    disabled=not has_api_key
)

if not has_api_key:
    st.caption("Connect a Gemini API key to enable content generation.")

# ----------------------------
# Prompt builders
# ----------------------------
def build_study_prompt(topic: str, grade: str, difficulty: str) -> str:
    return f"""
You are a highly effective school tutor.

Create a study package for this learner:
- Student level: {grade}
- Topic: {topic}
- Difficulty: {difficulty}

Return VALID JSON only.
Do not include markdown fences.
Do not include any text before or after the JSON.

Use this exact schema:
{{
  "topic_title": "string",
  "simple_explanation": "string",
  "key_points": ["string", "string", "string", "string", "string"],
  "practice_questions": [
    {{
      "question": "string",
      "difficulty": "easy|medium|hard"
    }},
    {{
      "question": "string",
      "difficulty": "easy|medium|hard"
    }},
    {{
      "question": "string",
      "difficulty": "easy|medium|hard"
    }}
  ],
  "answer_key": [
    "string",
    "string",
    "string"
  ],
  "common_mistakes": [
    "string",
    "string",
    "string"
  ],
  "study_tips": [
    "string",
    "string",
    "string"
  ]
}}
"""

def build_quiz_prompt(topic: str, grade: str, difficulty: str) -> str:
    return f"""
You are a school tutor.

Create a quiz for:
- Student level: {grade}
- Topic: {topic}
- Difficulty: {difficulty}

Return VALID JSON only.
Do not include markdown fences.
Do not include any text before or after the JSON.

Use this exact schema:
{{
  "topic_title": "string",
  "quiz_questions": [
    {{
      "question": "string",
      "expected_answer": "string"
    }},
    {{
      "question": "string",
      "expected_answer": "string"
    }},
    {{
      "question": "string",
      "expected_answer": "string"
    }}
  ]
}}
"""

def build_feedback_prompt(topic: str, question: str, expected_answer: str, student_answer: str, grade: str) -> str:
    return f"""
You are a patient tutor.

Evaluate the student's answer.

Student level: {grade}
Topic: {topic}
Question: {question}
Expected answer: {expected_answer}
Student answer: {student_answer}

Return VALID JSON only.
Do not include markdown fences.
Do not include any text before or after the JSON.

Use this exact schema:
{{
  "result": "correct|partly correct|incorrect",
  "feedback": "string",
  "improved_answer": "string",
  "next_tip": "string"
}}
"""

# ----------------------------
# Gemini call helper
# ----------------------------
def call_gemini(prompt: str, model_name: str):
    if not client:
        return None

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    text = response.text.strip()
    return json.loads(text)

# ----------------------------
# Session state
# ----------------------------
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "study_data" not in st.session_state:
    st.session_state.study_data = None

if "feedback_results" not in st.session_state:
    st.session_state.feedback_results = {}

# ----------------------------
# Generate study package
# ----------------------------
if generate_package and has_api_key:
    try:
        with st.spinner("Generating study package..."):
            data = call_gemini(build_study_prompt(topic, grade, difficulty), model_name)
            st.session_state.study_data = data
    except Exception:
        pass

# ----------------------------
# Generate quiz
# ----------------------------
if generate_quiz and has_api_key:
    try:
        with st.spinner("Generating quiz..."):
            data = call_gemini(build_quiz_prompt(topic, grade, difficulty), model_name)
            st.session_state.quiz_data = data
            st.session_state.feedback_results = {}
    except Exception:
        pass

# ----------------------------
# Render study package
# ----------------------------
study_data = st.session_state.study_data
if study_data:
    st.divider()
    st.subheader(study_data.get("topic_title", "Study Package"))

    st.markdown("### Simple Explanation")
    st.write(study_data.get("simple_explanation", ""))

    st.markdown("### Key Points")
    for item in study_data.get("key_points", []):
        st.write(f"- {item}")

    st.markdown("### Practice Questions")
    for i, q in enumerate(study_data.get("practice_questions", []), start=1):
        st.write(f"{i}. {q.get('question', '')}  \nDifficulty: {q.get('difficulty', '')}")

    st.markdown("### Answer Key")
    for i, ans in enumerate(study_data.get("answer_key", []), start=1):
        st.write(f"{i}. {ans}")

    st.markdown("### Common Mistakes")
    for item in study_data.get("common_mistakes", []):
        st.write(f"- {item}")

    st.markdown("### Study Tips")
    for item in study_data.get("study_tips", []):
        st.write(f"- {item}")

# ----------------------------
# Render quiz + answer checking
# ----------------------------
quiz_data = st.session_state.quiz_data
if quiz_data:
    st.divider()
    st.subheader(f"Quiz: {quiz_data.get('topic_title', topic)}")

    questions = quiz_data.get("quiz_questions", [])

    for i, q in enumerate(questions):
        st.markdown(f"### Question {i+1}")
        st.write(q.get("question", ""))

        answer_key = f"student_answer_{i}"
        button_key = f"check_answer_{i}"

        student_answer = st.text_area(
            f"Your answer for Question {i+1}",
            key=answer_key,
            height=100
        )

        check_clicked = st.button(
            f"Check Question {i+1}",
            key=button_key,
            disabled=not has_api_key
        )

        if check_clicked and has_api_key:
            try:
                with st.spinner(f"Checking Question {i+1}..."):
                    feedback = call_gemini(
                        build_feedback_prompt(
                            topic=quiz_data.get("topic_title", topic),
                            question=q.get("question", ""),
                            expected_answer=q.get("expected_answer", ""),
                            student_answer=student_answer,
                            grade=grade
                        ),
                        model_name
                    )
                    st.session_state.feedback_results[i] = feedback
            except Exception:
                pass

        if i in st.session_state.feedback_results:
            fb = st.session_state.feedback_results[i]

            result = fb.get("result", "").lower()
            if result == "correct":
                st.success(f"Result: {result}")
            elif result == "partly correct":
                st.warning(f"Result: {result}")
            else:
                st.error(f"Result: {result}")

            st.markdown("**Feedback**")
            st.write(fb.get("feedback", ""))

            st.markdown("**Improved Answer**")
            st.write(fb.get("improved_answer", ""))

            st.markdown("**Next Tip**")
            st.write(fb.get("next_tip", ""))

# ----------------------------
# Footer note
# ----------------------------
st.divider()
st.caption("Tip: Start with one narrow topic, such as quadratic functions, cell division, or acids and bases.")
