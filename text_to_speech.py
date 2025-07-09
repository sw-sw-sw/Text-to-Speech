import streamlit as st
import openai
import tempfile
import os
import datetime

'''
streamlit run text_to_speech.py
'''

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Streamlitアプリタイトル
st.title("Text-to-Speech with GPT-4o Mini TTS")

# --- APIキー入力 ---
st.sidebar.header("OpenAI Settings")
api_key = st.sidebar.text_input(
    "OpenAI API Key",
    value=OPENAI_API_KEY,  # デフォルト値としてkey.pyから取得
    type="password",
    help="ここにOpenAIのAPIキーを入力してください。"
)
if not api_key:
    st.sidebar.warning("APIキーが設定されていません。入力してください。")
openai.api_key = api_key

# --- TTSモデル設定 ---
st.sidebar.header("TTS Settings")
model = st.sidebar.selectbox(
    "Model",
    ["tts-1", "tts-1-hd"],
    help="使用するTTSモデルを指定"
)

# 日本語コンテンツの場合、FableとNovaが現在最も良い結果を出すとされています
voice_options = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

voice = st.sidebar.selectbox(
    "Voice",
    voice_options,
    help="使用する音声を選択"
)

# スピード調整（0.25倍から4倍まで）
speed = st.sidebar.slider(
    "Speed",
    min_value=0.25,
    max_value=4.0,
    value=1.0,
    step=0.05,
    help="音声の再生速度を調整（0.25x - 4.0x）"
)

# --- 出力フォーマット設定 ---
st.sidebar.header("Output Settings")
format_options = {
    "mp3": "MP3 (汎用性が高い)",
    "opus": "Opus (低遅延、Web最適化)",
    "aac": "AAC (Apple製品に最適)",
    "flac": "FLAC (ロスレス圧縮)",
    "wav": "WAV (非圧縮、高品質)"
}

selected_format = st.sidebar.selectbox(
    "Output Format",
    options=list(format_options.keys()),
    format_func=lambda x: format_options[x],
    help="出力する音声ファイルの形式を選択"
)

# --- メイン入力 ---
text_input = st.text_area(
    "Enter text to convert to speech:",
    value="The quick brown fox jumped over the lazy dog."
)

if st.button("Generate Speech"):
    # APIキー未入力チェック
    if not api_key:
        st.error("OpenAI APIキーが設定されていません。サイドバーに入力してください。")
    elif not text_input.strip():
        st.error("変換するテキストを入力してください。")
    else:
        with st.spinner("Generating audio..."):
            try:
                # 一時ファイル作成（選択されたフォーマットに応じて拡張子を変更）
                tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=f".{selected_format}")
                
                # 音声生成リクエスト（選択されたフォーマットを指定）
                with openai.audio.speech.with_streaming_response.create(
                    model=model,
                    voice=voice,
                    input=text_input,
                    speed=speed,
                    response_format=selected_format  # フォーマット指定を追加
                ) as response:
                    response.stream_to_file(tmpfile.name)

                # ファイルを読み込み再生
                audio_bytes = open(tmpfile.name, "rb").read()
                st.success("Audio generation complete!")
                
                # フォーマットに応じてMIMEタイプを設定
                mime_types = {
                    "mp3": "audio/mpeg",
                    "opus": "audio/opus", 
                    "aac": "audio/aac",
                    "flac": "audio/flac",
                    "wav": "audio/wav"
                }
                
                st.audio(audio_bytes, format=mime_types.get(selected_format, "audio/mpeg"))
                
                # 生成情報を表示
                st.info(f"Generated with speed: {speed}x, Format: {selected_format.upper()}")

                # --- 自動保存処理 ---
                # output_dir = "audio_output"
                # os.makedirs(output_dir, exist_ok=True)
                
                # # ファイル名例: output_20240611_153000.mp3
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # output_path = os.path.join(output_dir, f"output_{timestamp}.{selected_format}")
                
                # with open(tmpfile.name, "rb") as src, open(output_path, "wb") as dst:
                #     dst.write(src.read())
                    
                # st.success(f"Audio file saved to: {output_path}")
                
                # ダウンロードボタンの追加
                st.download_button(
                    label=f"Download {selected_format.upper()} file",
                    data=audio_bytes,
                    file_name=f"tts_output_{timestamp}.{selected_format}",
                    mime=mime_types.get(selected_format, "audio/mpeg")
                )

            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # 一時ファイルのクリーンアップ
                try:
                    os.unlink(tmpfile.name)
                except:
                    pass