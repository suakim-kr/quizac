import google.generativeai as genai
import pandas as pd
from file2txt import pdf_file_to_dataframe

# Gemini API 설정
genai.configure(api_key=st.secrets["api_keys"]["gemini"])
model = genai.GenerativeModel('gemini-1.5-flash')

def create_quiz_prompt(text_data, quiz_type='혼합'):
    prompt = (
        f"다음 텍스트를 기반으로 {quiz_type} 퀴즈를 생성해주세요.\n"
        "각 문제는 아래 형식을 엄격하게 따라야 합니다:\n\n"
        "문제 N (유형): 페이지 P\n"
        "문제: (문제 본문)\n"
        "보기:  (보기는 객관식일 경우만 포함)\n"
        "(a) ...\n"
        "(b) ...\n"
        "(c) ...\n"
        "(d) ...\n"
        "정답 N: (정답)\n"
        "해설 N: (왜 이게 정답인지 설명. 텍스트 근거를 바탕으로 구체적으로 작성)\n\n"
        "줄바꿈과 포맷을 절대 바꾸지 마세요. 마크다운 문법(별표, 볼드체 등)은 사용하지 마세요.\n\n"
        "예시:\n"
        "문제 1 (객관식): 페이지 5\n"
        "문제: Java에서 다형성을 설명하는 키워드는?\n"
        "보기:\n"
        "(a) extends\n"
        "(b) implements\n"
        "(c) override\n"
        "(d) final\n"
        "정답 1: (c)\n"
        "해설 1: override는 상속받은 메서드를 재정의할 때 사용되며, 다형성과 관련이 깊습니다.\n\n"
    )

    for idx, page_text in enumerate(text_data, start=1):
        prompt += f"[페이지 {idx}]\n{page_text}\n\n"

    return prompt


def generate_quiz_from_uploaded_pdf(file, model):
    df: pd.DataFrame = pdf_file_to_dataframe(file)
    text_data = df['cleaned_text'].dropna().tolist()
    prompt = create_quiz_prompt(text_data)
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini API 호출 중 오류 발생: {e}"
