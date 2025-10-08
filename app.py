import streamlit as st
import subprocess
import platform
import asyncio
import os
from agents import Agent, Runner

# ページ設定
st.set_page_config(
    page_title="AIエージェント - アプリ起動システム",
    page_icon="🤖",
    layout="wide"
)

# サイドバーでAPIキー入力
with st.sidebar:
    st.title("⚙️ 設定")
    api_key = st.text_input(
        "OpenAI APIキー",
        type="password",
        help="OpenAIのAPIキーを入力してください"
    )
    
    # APIキーを環境変数に設定
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    st.markdown("---")
    st.markdown("""
    ### 使い方
    1. APIキーを入力
    2. メッセージを送信
    3. AIがアプリを起動
    
    ### 例
    - 「メモ帳を開いて」
    - 「電卓を起動して」
    - 「ブラウザを開いて」
    """)

# アプリケーション起動関数をツールとして定義
def open_application(app_name: str) -> str:
    """
    指定されたアプリケーションを起動する
    
    Args:
        app_name: 起動するアプリケーション名 (例: メモ帳, 電卓, ブラウザ)
    
    Returns:
        実行結果のメッセージ
    """
    system = platform.system()
    
    try:
        if system == "Windows":
            app_commands = {
                "メモ帳": "notepad.exe",
                "notepad": "notepad.exe",
                "電卓": "calc.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "ブラウザ": "explorer.exe https://www.google.com",
                "browser": "explorer.exe https://www.google.com",
                "エクスプローラー": "explorer.exe",
                "explorer": "explorer.exe",
                "ペイント": "mspaint.exe",
                "paint": "mspaint.exe"
            }
        elif system == "Darwin":  # macOS
            app_commands = {
                "メモ帳": "open -a TextEdit",
                "notepad": "open -a TextEdit",
                "電卓": "open -a Calculator",
                "calculator": "open -a Calculator",
                "calc": "open -a Calculator",
                "ブラウザ": "open -a Safari",
                "browser": "open -a Safari",
                "safari": "open -a Safari",
                "ファインダー": "open -a Finder",
                "finder": "open -a Finder"
            }
        else:  # Linux
            app_commands = {
                "メモ帳": "gedit",
                "notepad": "gedit",
                "電卓": "gnome-calculator",
                "calculator": "gnome-calculator",
                "calc": "gnome-calculator",
                "ブラウザ": "xdg-open https://www.google.com",
                "browser": "xdg-open https://www.google.com",
                "ファイルマネージャー": "nautilus",
                "files": "nautilus"
            }
        
        # アプリケーション名を小文字で検索
        app_lower = app_name.lower().strip()
        command = None
        
        for key, cmd in app_commands.items():
            if key.lower() in app_lower or app_lower in key.lower():
                command = cmd
                break
        
        if command:
            if system == "Windows":
                subprocess.Popen(command.split(), shell=True)
            else:
                subprocess.Popen(command, shell=True)
            return f"✅ {app_name}を起動しました!"
        else:
            return f"❌ 申し訳ございません。{app_name}の起動方法が見つかりませんでした。"
    
    except Exception as e:
        return f"❌ エラーが発生しました: {str(e)}"

# エージェントの作成
agent = Agent(
    name="AppLauncher",
    instructions="""あなたはユーザーの要求に応じてアプリケーションを起動するアシスタントです。
ユーザーが「〜を開いて」「〜を起動して」などと言った場合、open_application関数を使用してアプリケーションを起動してください。
必ず関数を実行した後、その結果を日本語で分かりやすくユーザーに伝えてください。""",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "open_application",
                "description": "指定されたアプリケーションを起動する。メモ帳、電卓、ブラウザなどを開くことができます。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "起動するアプリケーション名 (例: メモ帳, 電卓, ブラウザ)"
                        }
                    },
                    "required": ["app_name"]
                },
                "implementation": open_application
            }
        }
    ],
)

# エージェントの実行関数
async def run_agent(user_message: str):
    """
    OpenAI Agents SDKを使用してエージェントを実行
    """
    # メッセージの実行
    result = await Runner.run(agent, user_message)
    
    return result

# メイン画面
st.title("🤖 AIエージェント - アプリ起動システム")
st.markdown("AIに話しかけてアプリケーションを起動しましょう!")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("メッセージを入力してください (例: メモ帳を開いて)"):
    if not api_key:
        st.error("⚠️ サイドバーからOpenAI APIキーを入力してください")
    else:
        # ユーザーメッセージを追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI応答処理
        with st.chat_message("assistant"):
            with st.spinner("処理中..."):
                try:
                    # 非同期関数を同期的に実行
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(run_agent(prompt))
                    loop.close()
                    
                    # デバッグ情報を表示
                    with st.expander("🔍 デバッグ情報", expanded=False):
                        st.write("**Result Type:**", type(result))
                        st.write("**Result:**", result)
                        if hasattr(result, '__dict__'):
                            st.write("**Result Attributes:**", result.__dict__)
                    
                    # 結果を取得
                    assistant_message = None
                    
                    # final_outputを確認
                    if hasattr(result, 'final_output'):
                        assistant_message = str(result.final_output)
                        st.markdown(assistant_message)
                    elif hasattr(result, 'messages') and result.messages:
                        # 最後のアシスタントメッセージを取得
                        for msg in reversed(result.messages):
                            if msg.role == "assistant" and hasattr(msg, 'content'):
                                if isinstance(msg.content, list):
                                    for content in msg.content:
                                        if hasattr(content, 'text'):
                                            assistant_message = content.text
                                            break
                                elif isinstance(msg.content, str):
                                    assistant_message = msg.content
                                if assistant_message:
                                    break
                        
                        if assistant_message:
                            st.markdown(assistant_message)
                        else:
                            assistant_message = "処理が完了しました。"
                            st.markdown(assistant_message)
                    else:
                        assistant_message = str(result)
                        st.markdown(assistant_message)
                    
                    # メッセージが取得できなかった場合のフォールバック
                    if not assistant_message:
                        assistant_message = "処理が完了しました。"
                        st.markdown(assistant_message)
                    
                    # アシスタントメッセージを保存
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                
                except Exception as e:
                    error_message = f"❌ エラーが発生しました: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })

# クリアボタン
if st.sidebar.button("🗑️ チャット履歴をクリア"):
    st.session_state.messages = []
    st.rerun()
