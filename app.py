import streamlit as st
import subprocess
import platform
import os
from openai import OpenAI

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

# アプリケーション起動関数
def open_application(app_name: str) -> str:
    """
    指定されたアプリケーションを起動する
    
    Args:
        app_name: 起動するアプリケーション名
    
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

# Function calling用のツール定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "ユーザーが要求したアプリケーションを起動します。メモ帳、電卓、ブラウザなどのアプリケーションを開くことができます。",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "起動するアプリケーションの名前 (例: メモ帳, 電卓, ブラウザ)"
                    }
                },
                "required": ["app_name"]
            }
        }
    }
]

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
                    client = OpenAI(api_key=api_key)
                    
                    # OpenAI APIを呼び出し
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "あなたはユーザーの要求に応じてアプリケーションを起動するアシスタントです。ユーザーが「〜を開いて」「〜を起動して」などと言った場合、open_application関数を使用してアプリケーションを起動してください。"},
                            *st.session_state.messages
                        ],
                        tools=tools,
                        tool_choice="auto"
                    )
                    
                    response_message = response.choices[0].message
                    tool_calls = response_message.tool_calls
                    
                    # Function callingの処理
                    if tool_calls:
                        for tool_call in tool_calls:
                            if tool_call.function.name == "open_application":
                                import json
                                args = json.loads(tool_call.function.arguments)
                                app_name = args.get("app_name")
                                
                                # アプリケーションを起動
                                result = open_application(app_name)
                                
                                # 結果を表示
                                st.markdown(result)
                                assistant_message = result
                    else:
                        # 通常の応答
                        assistant_message = response_message.content
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
