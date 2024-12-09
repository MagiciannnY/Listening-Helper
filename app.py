import os
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
from flask import render_template
import re
from pydub import AudioSegment
import whisper
from pydub.silence import split_on_silence
from openai import OpenAI
from flask_socketio import SocketIO, emit
import time;
from threading import Thread

# 智谱清言大模型
client = OpenAI(
    api_key="Your_API_KEY",
    base_url="model_url"
)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'mp3'}
socketio = SocketIO(app)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_audio():
    # 寻找上传的音频文件
    audio_dir = "uploads"
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]

    if len(audio_files) > 0:
        # 加载音频文件
        audio_file = audio_files[0]

        # 音频处理后的输出文件夹
        output = os.path.splitext(os.path.basename(audio_file))[0]
        os.makedirs("result", exist_ok=True)
        output_dir = os.path.join("result", output)
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建segments子文件夹
        segments_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_dir, exist_ok=True)

        audio = AudioSegment.from_mp3(os.path.join(audio_dir, audio_file))
        print("音频加载成功！")
        return audio, output, output_dir, segments_dir
    else:
        raise ValueError("没有新上传的音频文件！")

def process_audio(audio, segments_dir):
    # 载入 Whisper 模型
    model = whisper.load_model("base")

    segments = split_on_silence(audio, min_silence_len=750, silence_thresh=-40)
    
    # 识别每段音频的文本内容并保存音频
    transcripts = []
    for i, segment in enumerate(segments):
        # 保存每段音频到新文件夹中的segments子文件夹，按顺序命名
        segment_file = os.path.join(segments_dir, f"segment_{i + 1}.mp3")
        segment.export(segment_file, format="mp3")
        
        # 使用 Whisper 识别音频
        result = model.transcribe(segment_file)  
        transcripts.append(result['text'])
        
        # 将每段文本保存为txt文件
        transcript_file = os.path.join(segments_dir, f"segment_{i + 1}.txt")
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])

    # # 输出音频片段和对应的文本
    # for i, transcript in enumerate(transcripts):
    #     print(f"Segment {i + 1} Text: {transcript}")

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def create_html(audio_name):
    # 音频和文本文件存放的路径
    audio_dir = os.path.join("result", f"{audio_name}/segments")
    html_file = os.path.join("static", f"{audio_name}.html")

    # 获取所有音频文件和文本文件
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]
    text_files = [f for f in os.listdir(audio_dir) if f.endswith(".txt")]
    text_zh_dir = os.path.join(f"result/{audio_name}", "translated_texts")
    text_zh_files = [f for f in os.listdir(text_zh_dir) if f.endswith(".txt")]
    text_zh_files.sort(key=natural_sort_key)

    # 按自然排序对音频文件和文本文件排序
    audio_files.sort(key=natural_sort_key)
    text_files.sort(key=natural_sort_key)
    text_zh_files.sort(key=natural_sort_key)

    # 打开 HTML 文件，准备插入内容
    with open(html_file, "w", encoding="utf-8") as f:
        # 写入 HTML 文件头部
        f.write(f"""<!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{audio_name}</title>
        <link rel="stylesheet" href="styles.css">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: "Times New Roman", "宋体", "Arial", "Roboto", sans-serif;
            }}
        </style>
    </head>
    
    <body>
        <!-- 切换按钮 -->
        <button id="toggle-language-btn">EN</button>
        
        <div id="content">
    """)
        
        # 遍历音频和文本文件，生成每个段落的 HTML
        for i in range(len(audio_files)):
            audio_file = audio_files[i]
            text_file = text_files[i]
            text_zh_file = text_zh_files[i]

            # 读取文本内容
            with open(os.path.join(audio_dir, text_file), "r", encoding="utf-8") as text_f:
                text_content = text_f.read().strip()
                
            with open(os.path.join(text_zh_dir, text_zh_file), "r", encoding="utf-8") as text_zh_f:
                text_zh_content = text_zh_f.read().strip()

            f.write(f'    <p class="text-item" data-audio="{audio_file}" data-text-zh="{text_zh_content}" data-text="{text_content}">{text_content}</p>\n')

        # 写入 HTML 文件尾部
        f.write("""  </div>
        <audio id="audio-player" controls>
            <source id="audio-source" src="" type="audio/mpeg">
            您的浏览器不支持音频元素。
        </audio>

        <script src="script.js"></script>
    </body>
    </html>""")

    print("HTML 文件已生成！")

def translate_text_to_zh(text):
    """使用智谱清言大模型进行翻译(自行修改)"""
    completion = client.chat.completions.create(
        model="glm-4",  # 指定模型
        messages=[    
            {"role": "system", "content": "你是一个翻译专家，擅长将英文翻译为中文。"},    
            {"role": "user", "content": f"请将以下英文翻译为中文(注意只需要翻译结果，忽视句子错误，不添加新的内容)：\n\n{text}"}
        ],
        top_p=0.7,
        temperature=0.9
    )
    return completion.choices[0].message.content.strip()

def translate_files(input_directory, output_directory):
    """读取指定目录中的所有文本文件并翻译"""
    # 获取文件夹中的所有txt文件
    txt_files = [f for f in os.listdir(input_directory) if f.endswith('.txt')]

    for txt_file in txt_files:
        input_file_path = os.path.join(input_directory, txt_file)
        
        # 读取文本文件内容
        with open(input_file_path, 'r', encoding='utf-8') as file:
            text_content = file.read()

        # 翻译文本
        translated_text = translate_text_to_zh(text_content)

        # 保存翻译后的文本为新的文件
        output_file_path = os.path.join(output_directory, f"{os.path.splitext(txt_file)[0]}_zh.txt")
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
        print(f"文件 {txt_file} 已翻译并保存为 {os.path.basename(output_file_path)}")
        
def clear_uploads_folder():
    """清空 uploads 文件夹"""
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # 删除文件
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)  # 删除子目录（如果有）
            except Exception as e:
                print(f"无法删除 {file_path}: {e}")
    else:
        os.makedirs(app.config['UPLOAD_FOLDER'])  # 如果文件夹不存在，则创建


audio_name = ""

@app.route('/')
def index():
    # return send_from_directory('static', 'index.html')
    return render_template('index.html')

@app.route('/static')
def your_view_function():
    return render_template(f'{audio_name}.html', audio_name=audio_name)

@app.route('/result/<path:filename>')
def custom_static(filename):
    return send_from_directory('result', filename)

@app.route('/uploaded')
def uploaded():
    return render_template('uploaded.html')

def process_file_background(filename):
    try:
        # 发送开始处理的通知
        socketio.emit('start_process', {'filename': filename})
        
        # 示例的文件处理逻辑
        audio, audio_name, output_dir, segments_dir = load_audio()
        process_audio(audio, segments_dir)
        inputFile = os.path.join("result", f"{audio_name}/segments")
        translated_dir = os.path.join(f"result/{audio_name}", "translated_texts")
        if not os.path.exists(translated_dir):
            os.makedirs(translated_dir)
        translate_files(inputFile, translated_dir)
        create_html(audio_name)
        
        # 清空上传目录
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # 发送处理完成通知
        socketio.emit('finish_process', {'filename': filename})
        
    except Exception as e:
        # 发送错误通知
        socketio.emit('error_process', {'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return '没有文件部分', 400
    file = request.files['file']
    if file.filename == '':
        return '没有选择文件', 400
    if file and allowed_file(file.filename):
        # 确保上传文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        # 保存文件
        filename = secure_filename(file.filename).lower()
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # 渲染 progress.html 页面
        thread = Thread(target=process_file_background, args=(filename,))
        thread.start()
        return render_template('progress.html', filename=filename)

    return '文件类型不被允许', 400

if __name__ == '__main__':
    clear_uploads_folder()
    app.run(debug=True, port=5001)
