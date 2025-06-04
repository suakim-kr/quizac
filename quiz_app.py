import streamlit as st
import json
from file2txt import pdf_file_to_dataframe
from quiz_gen import generate_quiz_from_uploaded_pdf, model
import re

st.markdown("""
    <h1 style='text-align: center;'> Quizac </h1>
    <p style='text-align: center; font-size: 16px; color: gray;'>
        PDF만 올리면 퀴즈 시작!<br>
        강의 자료나 필기 내용을 퀴즈로 만들어 드릴게요 ✨
    </p>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDF 파일 업로드하기", type="pdf")

if uploaded_file:
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        start_button = st.button("퀴즈 생성하기", use_container_width=True)

    if start_button:
        with st.spinner("퀴즈를 만들고 있어요..."):
            # Gemini 호출
            raw_quiz = generate_quiz_from_uploaded_pdf(uploaded_file, model)
            st.session_state['raw_quiz'] = raw_quiz
            
            # 파싱
            quiz_blocks = re.split(r'(?:^|\n)(?=문제 \d+ \([^)]+\):)', raw_quiz.strip())

            quiz_data = []

            for block in quiz_blocks:
                number_match = re.search(r'문제 (\d+) \(([^)]+)\): 페이지 (\d+)', block)
                if not number_match:
                    continue
                number, q_type, page = number_match.groups()

                # 정답/해설 추출 (강제 구간 자르기)
                answer_match = re.search(r'정답\s*\d+\s*:\s*(.*)', block)
                explanation_match = re.search(r'해설\s*\d+\s*:\s*(.*)', block)

                # 해설에서 다음 문제 제목까지 들어가는 경우를 제거
                explanation = ""
                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                    explanation = re.split(r'\n문제 \d+ \([^)]+\):', explanation)[0].strip()

                # 문제 본문만 추출
                question_text = ""
                block_lines = block.split('\n')
                for i, line in enumerate(block_lines):
                    if line.strip().startswith('정답'):
                        question_text = '\n'.join(block_lines[0:i]).strip()  # 0부터 시작
                        break

                quiz_data.append({
                    "번호": int(number),
                    "유형": q_type.strip(),
                    "페이지": int(page),
                    "문제": question_text,
                    "정답": answer_match.group(1).strip() if answer_match else "",
                    "해설": explanation
                })

            st.session_state['quiz_data'] = quiz_data
            st.success("퀴즈 생성 완료!")

# 퀴즈 풀기 화면
if 'quiz_data' in st.session_state:
    quiz_data = st.session_state['quiz_data']
    for i, q in enumerate(quiz_data):
        question_lines = q['문제'].split('\n')
        question_numbered = f"**Q{i+1}.** {question_lines[0]}"
        question_body = '<br>'.join(question_lines[1:])

        st.markdown(f"{question_numbered}<br><br>{question_body}", unsafe_allow_html=True)

        if q['정답'] in ['O', 'X']:
            user_answer = st.radio("O/X를 선택하세요:", ['O', 'X'], key=f"q{i}")
        elif q['정답'].startswith('(') and ')' in q['정답']:
            choices = ['(a)', '(b)', '(c)', '(d)']
            user_answer = st.radio("보기 중에서 선택하세요:", choices, key=f"q{i}")
        else:
            user_answer = st.text_input("정답을 입력하세요:", key=f"q{i}")

        if st.button(f"정답 확인 (Q{i+1})", key=f"btn{i}"):
            if user_answer.strip() == q['정답'].strip():
                st.success("정답입니다!")
            else:
                st.error(f"오답입니다! 정답: {q['정답']}")
            st.info(f"해설: {q['해설']}")

if 'quiz_data' in st.session_state and 'raw_quiz' in st.session_state:
    st.markdown("---")
    st.download_button(
        label="📥 선생님용 문제 다운로드하기",
        data=st.session_state['raw_quiz'],
        file_name="quiz_output.txt",
        mime="text/plain"
    )
