
import os
import base64
from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Note Drop</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-x: hidden;
        }
        .terminal {
            background: #000;
            border: 2px solid #00ff00;
            border-radius: 8px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 0 30px rgba(0,255,0,0.3);
            position: relative;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { box-shadow: 0 0 30px rgba(0,255,0,0.3); }
            to { box-shadow: 0 0 50px rgba(0,255,0,0.6); }
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            font-size: 18px;
            opacity: 0.8;
        }
        .input-group {
            position: relative;
            margin-bottom: 25px;
        }
        textarea {
            width: 100%;
            height: 160px;
            background: #000;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            border-radius: 4px;
            resize: vertical;
            caret-color: #00ff00;
        }
        textarea::placeholder {
            color: #008800;
        }
        textarea:focus {
            outline: none;
            border-color: #00ff41;
            box-shadow: 0 0 10px rgba(0,255,0,0.5);
        }
        .btn {
            width: 100%;
            padding: 18px;
            background: #00ff00;
            color: #000;
            border: none;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover {
            background: #00cc00;
            box-shadow: 0 0 20px rgba(0,255,0,0.6);
            transform: translateY(-2px);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn:disabled {
            background: #333;
            color: #666;
            cursor: not-allowed;
            box-shadow: none;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            display: none;
            border-left: 4px solid;
        }
        .success {
            background: rgba(0,255,0,0.1);
            border-color: #00ff00;
            color: #00ff41;
        }
        .error {
            background: rgba(255,0,0,0.1);
            border-color: #ff4444;
            color: #ff6666;
        }
        .blink {
            animation: blink 1s infinite;
        }
        @keyframes blink {
            50% { opacity: 0.3; }
        }
        .prompt {
            color: #008800;
            font-size: 14px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="terminal">
        <div class="header">
            <div>user@pentest:~$ Secure Note Drop</div>
            <div style="font-size:14px;opacity:0.6;margin-top:5px;">(I have permission and am authorized to perform this pentest)</div>
        </div>
        
        <div class="prompt">$ enter payload:</div>
        <div class="input-group">
            <textarea id="note" placeholder="Payload / Note / Command... (Ctrl+Enter to inject)"></textarea>
        </div>
        
        <button class="btn" onclick="injectPayload()">INJECT PAYLOAD</button>
        
        <div id="status" class="status"></div>
    </div>

    <script>
        async function injectPayload() {
            const note = document.getElementById('note').value.trim();
            const status = document.getElementById('status');
            const btn = document.querySelector('.btn');
            
            if (!note) {
                showStatus('[-] Empty payload rejected', 'error');
                return;
            }
            
            btn.textContent = 'INJECTING...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/inject', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({payload: note})
                });
                
                const data = await res.json();
                
                if (data.success) {
                    showStatus('[+] Payload injected successfully | Target: notes.txt', 'success');
                    document.getElementById('note').value = '';
                } else {
                    showStatus('[-] Injection failed: ' + (data.error || 'unknown'), 'error');
                }
            } catch (e) {
                showStatus('[-] Connection dropped', 'error');
            }
            
            btn.textContent = 'INJECT PAYLOAD';
            btn.disabled = false;
        }
        
        function showStatus(msg, type) {
            const status = document.getElementById('status');
            status.textContent = msg;
            status.className = `status ${type}`;
            status.style.display = 'block';
            setTimeout(() => status.style.display = 'none', 5000);
        }
        
        // Ctrl+Enter
        document.addEventListener('keydown', e => {
            if (e.ctrlKey && e.key === 'Enter') injectPayload();
        });
        
        // Auto-focus
        document.getElementById('note').focus();
    </script>
</body>
</html>
'''

@app.route('/inject', methods=['POST'])
def inject():
    try:
        data = request.get_json()
        payload = data['payload']
        
        token = os.getenv('GITHUB_TOKEN')
        user = os.getenv('GITHUB_USERNAME')
        repo = os.getenv('REPO_NAME')
        path = os.getenv('FILE_PATH', 'notes.txt')
        
        if not all([token, user, repo]):
            return jsonify({'error': 'Config error'})
        
        url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
        headers = {'Authorization': f'token {token}'}
        
        # Get file
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            file_data = r.json()
            content = base64.b64decode(file_data['content']).decode()
            sha = file_data['sha']
        else:
            content = ''
            sha = None
        
        # Add payload
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_content = content + f"\n[{timestamp}] {payload}"
        
        # Commit
        commit_data = {
            'message': f'Payload [{timestamp}]',
            'content': base64.b64encode(new_content.encode()).decode(),
            'sha': sha
        }
        
        r = requests.put(url, headers=headers, json=commit_data)
        
        return jsonify({
            'success': r.status_code in [200, 201]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
