
import os
import base64
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head><title>GitHub Note Saver</title>
<style>
body {font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;background:#f5f5f5;}
textarea {width:100%;height:150px;padding:15px;border:1px solid #ddd;border-radius:8px;font-size:16px;}
button {width:100%;padding:15px;background:#007cba;color:white;border:none;border-radius:8px;font-size:18px;cursor:pointer;}
button:hover {background:#005a87;}
#status {margin-top:15px;padding:10px;border-radius:5px;display:none;}
.success {background:#d4edda;color:#155724;}
.error {background:#f8d7da;color:#721c24;}
</style>
</head>
<body>
<h1>📝 GitHub Note Saver</h1>
<textarea id="note" placeholder="তোমার নোট লিখো... Ctrl+Enter চাপো"></textarea><br>
<button onclick="saveNote()">💾 Save to GitHub</button>
<div id="status"></div>

<script>
async function saveNote(){
  const note = document.getElementById('note').value.trim();
  const status = document.getElementById('status');
  const btn = document.querySelector('button');
  
  if(!note){
    showStatus('কিছু লিখো!','error');
    return;
  }
  
  btn.textContent = 'Saving...';
  btn.disabled = true;
  
  try{
    const res = await fetch('/save', {
      method: 'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({note})
    });
    const data = await res.json();
    
    if(data.success){
      showStatus('✅ সফল! GitHub এ সেভ হয়েছে','success');
      document.getElementById('note').value = '';
    } else {
      showStatus(data.error || 'Error!','error');
    }
  }catch(e){
    showStatus('Network error!','error');
  }
  
  btn.textContent = '💾 Save to GitHub';
  btn.disabled = false;
}

function showStatus(msg,type){
  const status = document.getElementById('status');
  status.textContent = msg;
  status.className = type;
  status.style.display = 'block';
  setTimeout(()=>status.style.display='none', 4000);
}

document.addEventListener('keydown', e=>{
  if(e.ctrlKey && e.key==='Enter') saveNote();
});
</script>
</body>
</html>
'''

@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.get_json()
        note = data['note']
        
        token = os.getenv('GITHUB_TOKEN')
        user = os.getenv('GITHUB_USERNAME') 
        repo = os.getenv('REPO_NAME')
        path = os.getenv('FILE_PATH', 'notes.txt')
        
        if not all([token, user, repo]):
            return jsonify({'error': 'Missing GitHub config!'})
        
        url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}"
        headers = {'Authorization': f'token {token}'}
        
        # Get existing file
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            file_data = r.json()
            content = base64.b64decode(file_data['content']).decode()
            sha = file_data['sha']
        else:
            content = ''
            sha = None
        
        # Add new line
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_content = content + f"\n{timestamp} | {note}"
        
        # Update file
        payload = {
            'message': f'Add note: {timestamp}',
            'content': base64.b64encode(new_content.encode()).decode(),
            'sha': sha
        }
        
        r = requests.put(url, headers=headers, json=payload)
        
        return jsonify({
            'success': r.status_code in [200, 201],
            'message': 'Saved!' if r.status_code in [200, 201] else f'Error {r.status_code}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
