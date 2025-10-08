import streamlit as st
from openai import OpenAI, AzureOpenAI
import time
import json

# ページ設定
st.set_page_config(
    page_title="AIエージェント - 質問回答システム",
    page_icon="🤖",
    layout="wide"
)

# タイトル
st.title("🤖 AIエージェント - 質問回答システム")
st.markdown("質問を入力すると、AIが回答を記載したファイルを生成します。")

# サイドバーでAPIキー設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    # API選択
    api_type = st.radio("API種類を選択", ["OpenAI", "Azure OpenAI"])
    
    if api_type == "OpenAI":
        api_key = st.text_input("OpenAI APIキー", type="password", key="api_key")
    else:
        api_key = st.text_input("Azure OpenAI APIキー", type="password", key="api_key")
        azure_endpoint = st.text_input("Azure エンドポイント", 
                                       placeholder="https://your-resource.openai.azure.com/",
                                       key="azure_endpoint")
        deployment_name = st.text_input("デプロイメント名", 
                                       placeholder="gpt-4o",
                                       key="deployment_name")
        api_version = st.text_input("APIバージョン", 
                                    value="2024-05-01-preview",
                                    key="api_version")
    
    st.markdown("---")
    st.markdown("### 使い方")
    st.markdown("""
    1. API種類を選択
    2. 必要な情報を入力
    3. 質問を入力して送信
    4. AIエージェントが回答ファイルを生成
    5. ファイルをダウンロード
    """)

# メインエリア
if not api_key:
    st.warning("⚠️ サイドバーからAPIキーを入力してください。")
    st.stop()

if api_type == "Azure OpenAI" and (not azure_endpoint or not deployment_name):
    st.warning("⚠️ Azure エンドポイントとデプロイメント名を入力してください。")
    st.stop()

# クライアント初期化
if api_type == "OpenAI":
    client = OpenAI(api_key=api_key)
    model_name = "gpt-4o"
else:
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint
    )
    model_name = deployment_name

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

# アシスタントの作成（初回のみ）
if st.session_state.assistant_id is None:
    try:
        with st.spinner("AIエージェントを初期化中..."):
            assistant = client.beta.assistants.create(
                name="質問回答エージェント",
                instructions="""あなたは質問に対して詳細な回答を提供するエージェントです。
                ユーザーからの質問を受け取ったら、以下の形式で回答してください：
                
                1. 質問の要約
                2. 詳細な回答
                3. 関連情報や補足事項
                
                回答は分かりやすく、構造化された形式で提供してください。""",
                model=model_name,
                tools=[{"type": "file_search"}]
            )
            st.session_state.assistant_id = assistant.id
            st.success("✅ AIエージェントの初期化が完了しました")
    except Exception as e:
        st.error(f"エラー: {str(e)}")
        st.stop()

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "file_data" in message:
            st.download_button(
                label="📄 回答ファイルをダウンロード",
                data=message["file_data"],
                file_name=message["file_name"],
                mime="text/plain"
            )

# ユーザー入力
if prompt := st.chat_input("質問を入力してください..."):
    # ユーザーメッセージを追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # アシスタントの応答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # スレッドの作成
            thread = client.beta.threads.create()
            
            # メッセージの追加
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            
            # 実行の開始
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=st.session_state.assistant_id
            )
            
            # 実行完了を待つ
            with st.spinner("回答を生成中..."):
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
            
            if run.status == "completed":
                # メッセージの取得
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                assistant_message = messages.data[0].content[0].text.value
                
                # 回答を表示
                message_placeholder.markdown(assistant_message)
                
                # ファイルの生成
                file_content = f"""質問回答レポート
{'='*50}

【質問】
{prompt}

{'='*50}

【回答】
{assistant_message}

{'='*50}
生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                file_name = f"回答_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                
                # ダウンロードボタン
                st.download_button(
                    label="📄 回答ファイルをダウンロード",
                    data=file_content,
                    file_name=file_name,
                    mime="text/plain"
                )
                
                # セッションに保存
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                    "file_data": file_content,
                    "file_name": file_name
                })
            else:
                st.error(f"エラー: 実行ステータス - {run.status}")
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

# フッター
st.markdown("---")
st.markdown("💡 **ヒント**: 具体的な質問をすると、より詳細な回答が得られます。")
