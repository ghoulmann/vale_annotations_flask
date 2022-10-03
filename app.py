import os
from io import StringIO
import subprocess
import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

from flask import Flask, render_template, request, redirect, url_for



app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    with open("/tmp/output_file", "bw") as f:
        chunk_size = 4096
        while True:
            chunk = request.stream.read(chunk_size)
            if len(chunk) == 0:
                return
            f.write(chunk)
@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['md_file']
    source = str(uploaded_file.getvalue(), 'utf-8')
    file = StringIO(source)
    
    #lint = subprocess.run(['vale', '--ext=.md', '--config="vale/.vale.ini"', source], capture_output=True, text=True)
    #print(lint.stdout)
    print(source)
    valeconfig = "valeconfig/vale.ini"
    lint = subprocess.run(['/snap/bin/vale', "--ext=.md", "--config=" + valeconfig, source], capture_output=True, text=True)
    print(lint.stdout)
    #lint = subprocess.run(['vale', 'config="./.vale.ini"', source], capture_output=True, text=True)
    

    


    md = markdown.markdown(source, extensions=['mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 

    return render_template('layout.html', content=md)
    #uploaded_file = request.files['md_file']
    #if uploaded_file.filename != '':
    #    uploaded_file.save(uploaded_file.filename)
    #    with open(uploaded_file.filename, 'r') as f:
    #        source = f.read()
        # md = markdown.markdown(source, extensions=['mdx_truly_sane_lists', 'fenced_code', 'extra', 'toc', 'smarty', 'pymdownx.superfences', 'pymdownx.highlight'], output_format="html5") 
    #return render_template('layout.html', content=md)
    
    
if __name__ == '__main__':
   app.run(debug = True)
