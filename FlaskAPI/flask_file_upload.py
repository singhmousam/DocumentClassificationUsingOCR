import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/home/ikscare/Documents/Projects/Mousam/FlaskAPI'
ALLOWED_EXTENSIONS = set(['pdf'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('runDocumentManager',input_path=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/runDocumentManager', methods=["POST",'GET'])
def runDocumentManager():
	return 'Done'+UPLOAD_FOLDER

@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
	    # Get the name of the uploaded files
	    uploaded_files = request.files.getlist("file[]")
	    filenames = []
	    for file in uploaded_files:
	        # Check if the file is one of the allowed types/extensions
	        if file and allowed_file(file.filename):
	            # Make the filename safe, remove unsupported chars
	            filename = secure_filename(file.filename)
	            # Move the file form the temporal folder to the upload
	            # folder we setup
	            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	            # Save the filename into a list, we'll use it later
	            filenames.append(filename)
	            # Redirect the user to the uploaded_file route, which
	            # will basicaly show on the browser the uploaded file
	    # Load an html page with a link to each uploaded file
    #return render_template('upload.html', filenames=filenames)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
### Working method for multiple file upload
filenames = []
@app.route('/uploads',methods = ['GET','POST'])
def upload_file1():
    if request.method =='POST':
        uploadedFiles = request.files.getlist('file[]')
        for file in uploadedFiles :
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            filenames.append(filename)
        return redirect(url_for('confirm'))
    return """<!doctype html>
<title>Upload new File</title>
<h1>Upload new File</h1>
<form action='' method="POST" enctype="multipart/form-data">
    <p><input type='file' name='file[]' multiple=''>
    <input type='submit' value='upload'>
    </p>

</form>"""


@app.route('/confirm')
def confirm():
	return render_template('confirm.html', numOfFiles=len(filenames), files=filenames)

	
if __name__ == '__main__':
    app.run(host='0.0.0.0')