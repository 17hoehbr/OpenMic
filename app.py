import socket
import qrcode
import os
import threading
from yt_dlp import YoutubeDL
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_httpauth import HTTPDigestAuth
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

app.secret_key = os.urandom(12).hex()
auth = HTTPDigestAuth()

users = {
    "bryce": "bryce"
}

queue = []

@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

# ---------------- Mobile Routes ----------------

@app.route("/")
def index():
    return render_template("mobile_index.html", active="home")

@app.route("/queue")
def queue():
    return render_template("queue.html", active="queue")

@app.route("/search", methods=['GET', 'POST'])
def search():
    result = ''
    if request.method == 'POST':
        if 'song' in request.form:
            song = request.form['song']
            
            #download_thread = threading.Thread(target=download_video, args=(song,))
            #download_thread.start()

            num_results = 5
            yt_search = f'ytsearch{num_results}:"{song} karaoke"'

            ydl_opts = {
                'format': 'best',   # You can specify the format you want
                'extract_flat': True,
                'extract_no_playlists': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f'{yt_search}', download=False)
            
        elif 'url' in request.form:
            url = request.form['url']
            
            download_thread = threading.Thread(target=download_video, args=(url,))
            download_thread.start()

    return render_template("search.html", active="search", result=result)


@app.route("/admin", methods=['GET', 'POST'])
#@auth.login_required
def admin():
    if request.method == 'POST':
        if 'restart' in request.form:
            # Execute your JavaScript code to restart playback
            socketio.emit('player_restart')
        elif 'pause' in request.form:
            # Execute your JavaScript code to pause/resume playback
            socketio.emit('player_pause')
        elif 'skip' in request.form:
            # Execute your JavaScript code to skip playback
            socketio.emit('player_skip')
    return render_template("admin.html", active="admin")

# ---------------- TV Routes ----------------

@app.route("/tv")
def tv():
    # get local ip address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.0.0.0", 0))

    local_ip = s.getsockname()[0]
    qr = qrcode.make(local_ip)
    qr.save("./static/qrcode.png")

    return render_template("tv_index.html", local_ip=local_ip)

@app.route('/play_video')
def play_video():
    return render_template("video_player.html")

# ---------------- Functions ----------------


def download_video(song):
    output = './static/video.mp4'

    ydl_opts = {
        'outtmpl': output,
        'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'ytsearch:{song} karaoke'])

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)