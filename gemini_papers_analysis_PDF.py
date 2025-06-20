import os
import json
import streamlit as st
import PyPDF2
import google.generativeai as genai

# === 설치가 필요한 패키지 ===
# pip install streamlit PyPDF2 google-generativeai

# === Gemini API 설정 ===
genai.configure(api_key="YOUR_API_KEY_HERE")
model = genai.GenerativeModel("gemini-1.5-flash")

st.title("📄 PDF 기반 논문 분석 시스템")

# ——— PDF 파일 다중 업로드 ———
uploaded_pdfs = st.file_uploader(
    "분석할 PDF 파일을 여러 개 업로드하세요 (.pdf):",
    type=["pdf"],
    accept_multiple_files=True
)

question = st.text_input("AI에게 물어볼 질문을 입력하세요:")
ask = st.button("질문하기")

if ask:
    if not uploaded_pdfs:
        st.warning("PDF 파일을 하나 이상 업로드해주세요.")
    elif not question:
        st.warning("질문 내용을 입력해주세요.")
    else:
        context_list = []
        download_files = []  # to store paths for download buttons

        # 1) PDF → 텍스트 추출 → .txt, .json 생성
        for pdf_file in uploaded_pdfs:
            # 읽기
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            # 파일 이름 설정
            base_name = os.path.splitext(pdf_file.name)[0]
            txt_path  = f"{base_name}.txt"
            json_path = f"{base_name}.json"

            # 2) .txt 저장
            with open(txt_path, "w", encoding="utf-8") as f_txt:
                f_txt.write(text)

            # 3) .json 저장
            with open(json_path, "w", encoding="utf-8") as f_json:
                json.dump(
                    {"filename": pdf_file.name, "text": text},
                    f_json,
                    ensure_ascii=False,
                    indent=2
                )

            # context 준비
            header = f"📄 파일: {pdf_file.name}\n"
            context_list.append(header + text)

            download_files.append((txt_path, json_path))

        # 4) Gemini 호출
        full_context = "\n\n---\n\n".join(context_list)
        prompt = (
            "다음은 여러 논문에서 추출한 내용입니다. 이 내용을 바탕으로 아래 질문에 답해주세요.\n\n"
            f"{full_context}\n\n"
            f"[질문]\n{question}"
        )
        response = model.generate_content(prompt)

        # 5) 결과 출력
        st.subheader("🧠 AI의 응답:")
        st.write(response.text)

        # 6) 변환된 파일 다운로드
        st.subheader("🔄 변환된 파일 다운로드")
        for txt_path, json_path in download_files:
            with open(txt_path, "rb") as f:
                st.download_button(
                    label=f"{os.path.basename(txt_path)} 다운로드",
                    data=f,
                    file_name=os.path.basename(txt_path),
                )
            with open(json_path, "rb") as f:
                st.download_button(
                    label=f"{os.path.basename(json_path)} 다운로드",
                    data=f,
                    file_name=os.path.basename(json_path),
                )
