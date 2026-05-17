from flask import Flask, request, redirect, url_for, session, render_template, send_from_directory
from web3 import Web3, HTTPProvider
import hashlib
import json
import os
import pickle
import ipfsApi

app = Flask(__name__)
app.secret_key = "edasvic_secret"

# ------------------------------------------------
# Blockchain Connection
# ------------------------------------------------

blockchain_address = 'http://127.0.0.1:8545'
web3 = Web3(HTTPProvider(blockchain_address))

account = web3.eth.accounts[0]

contract_address = "0x2c20fE40BB2C29E5460537cDbb9B08F18f8EB6e8"

with open('build/contracts/EDASVICStorageVerification.json') as f:
    contract_json = json.load(f)
    contract_abi = contract_json['abi']

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# ------------------------------------------------
# IPFS Connection
# ------------------------------------------------

api = ipfsApi.Client(host='127.0.0.1', port=5001)


# ------------------------------------------------
# Register User
# ------------------------------------------------

@app.route('/RegisterAction', methods=['POST'])
def RegisterAction():

    username = request.form['username']
    fullname = request.form['fullname']
    email = request.form['email']
    mobile = request.form['mobile']
    password = request.form['password']
    role = int(request.form['role'])

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if contract.functions.userExists(username).call():
        return render_template('register.html', error="Username already exists. Please choose another.")
    else:
        contract.functions.registerUser(
            username,
            fullname,
            email,
            mobile,
            password_hash,
            role
        ).transact({'from': account})

    return redirect(url_for('Login'))

# ------------------------------------------------
# Login
# ------------------------------------------------

@app.route('/LoginAction', methods=['POST'])
def LoginAction():

    username = request.form['username']
    password = request.form['password']

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    status = contract.functions.loginUser(
        username,
        password_hash
    ).call()

    if status:

        session['username'] = username

        user = contract.functions.getUser(username).call()
        role = user[4]

        if role == 1:
            return redirect(url_for('OwnerDashboard'))

        if role == 2:
            return redirect(url_for('VerifierDashboard'))

    return "<h3 align=center>Login Failed</h3>"


# ------------------------------------------------
# Upload File
# ------------------------------------------------

@app.route('/UploadFile', methods=['POST'])
def UploadFile():

    file = request.files['file']
    filename = file.filename

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    chunk_size = 1024 * 256

    chunks = []

    with open(filepath, "rb") as f:

        while True:

            piece = f.read(chunk_size)

            if piece == b"":
                break

            chunks.append(piece)

    chunk_hashes = []
    cids = []

    for i in range(len(chunks)):

        chunk_hash = hashlib.sha256(chunks[i]).hexdigest()
        chunk_hashes.append(chunk_hash)

        content = pickle.dumps(chunks[i])

        cid = api.add_pyobj(content)

        cids.append(cid)

    # -------------------------------
    # Merkle Tree Root Generation
    # -------------------------------

    hashes = chunk_hashes.copy()

    while len(hashes) > 1:

        new_hashes = []

        for i in range(0, len(hashes), 2):

            if i+1 < len(hashes):
                combined = hashes[i] + hashes[i+1]
            else:
                combined = hashes[i]

            h = hashlib.sha256(combined.encode()).hexdigest()
            new_hashes.append(h)

        hashes = new_hashes

    merkle_root = hashes[0]

    username = session['username']

    total_chunks = len(chunks)

    contract.functions.uploadFile(
        filename,
        username,
        merkle_root,
        total_chunks
    ).transact({'from': account})

    file_id = contract.functions.getTotalFiles().call()

    for i in range(total_chunks):

        contract.functions.storeChunk(
            file_id,
            i,
            cids[i],
            chunk_hashes[i]
        ).transact({'from': account})

    chunks = []
    for i in range(total_chunks):
        chunks.append({
            "chunk": i,
            "cid": cids[i],
            "hash": chunk_hashes[i]
        })

    return render_template(
        'chunk_details.html',
        filename=filename,
        owner=username,
        merkle=merkle_root,
        chunks=chunks
    )

# ------------------------------------------------
# View Files
# ------------------------------------------------

@app.route('/ViewFiles', methods=['GET'])
def ViewFiles():

    total = contract.functions.getTotalFiles().call()

    files = []

    for i in range(1,total+1):

        f = contract.functions.getFileDetails(i).call()

        files.append({
            "id": i,
            "name": f[0],
            "owner": f[1],
            "root": f[2],
            "chunks": f[3]
        })

    back_url = '/'
    username = session.get('username')
    if username:
        user = contract.functions.getUser(username).call()
        role = user[4]
        if role == 1:
            back_url = url_for('OwnerDashboard')
        elif role == 2:
            back_url = url_for('VerifierDashboard')

    return render_template('files.html', files=files, back_url=back_url)

# ------------------------------------------------
# View Chunks
# ------------------------------------------------

def _get_chunks_for_file(file_id):
    total_chunks = contract.functions.getChunkCount(file_id).call()
    chunks = []

    for i in range(total_chunks):
        c = contract.functions.getChunkDetails(file_id, i).call()
        chunks.append({
            "chunkId": c[0],
            "cid": c[1],
            "hash": c[2]
        })

    return chunks

@app.route('/ViewChunks')
def ViewChunks():

    file_id = int(request.args.get("file_id"))

    chunks = _get_chunks_for_file(file_id)
    return render_template('chunks.html', chunks=chunks)

@app.route('/chunks/<int:file_id>')
def ViewChunksById(file_id):
    chunks = _get_chunks_for_file(file_id)
    return render_template('chunks.html', chunks=chunks)

# ------------------------------------------------
# Download Chunk
# ------------------------------------------------

def _download_chunk_to_static(cid):
    content = api.get_pyobj(cid)
    content = pickle.loads(content)

    chunks_dir = os.path.join("static", "chunks")
    os.makedirs(chunks_dir, exist_ok=True)
    chunk_path = os.path.join(chunks_dir, cid)

    if os.path.exists(chunk_path):
        os.remove(chunk_path)

    with open(chunk_path, "wb") as file:
        file.write(content)

    file.close()

    return send_from_directory(
        chunks_dir,
        cid,
        as_attachment=True,
        download_name=f"{cid}.bin"
    )

@app.route('/DownloadChunk')
def DownloadChunk():

    cid = request.args.get("cid")

    return _download_chunk_to_static(cid)

@app.route('/download/<cid>')
def DownloadChunkById(cid):
    return _download_chunk_to_static(cid)

# ------------------------------------------------
# Verify File
# ------------------------------------------------

def _verify_file_status(file_id):
    f = contract.functions.getFileDetails(file_id).call()
    stored_root = f[2]

    hashes = []

    total_chunks = contract.functions.getChunkCount(file_id).call()

    for i in range(total_chunks):
        c = contract.functions.getChunkDetails(file_id, i).call()
        cid = c[1]
        content = api.get_pyobj(cid)
        content = pickle.loads(content)
        h = hashlib.sha256(content).hexdigest()
        hashes.append(h)

    while len(hashes) > 1:
        new_hash = []

        for i in range(0, len(hashes), 2):
            if i+1 < len(hashes):
                combined = hashes[i] + hashes[i+1]
            else:
                combined = hashes[i]

            nh = hashlib.sha256(combined.encode()).hexdigest()
            new_hash.append(nh)

        hashes = new_hash

    calculated_root = hashes[0]

    return stored_root == calculated_root

@app.route('/VerifyFile')
def VerifyFile():

    file_id = int(request.args.get("file_id"))

    status = _verify_file_status(file_id)
    return render_template('verify_result.html', status=status)

@app.route('/verify/<int:file_id>')
def VerifyFileById(file_id):
    status = _verify_file_status(file_id)
    return render_template('verify_result.html', status=status)

# ------------------------------------------------
# Logout
# ------------------------------------------------

@app.route('/Logout')
def Logout():

    session.clear()

    return redirect('/')

# ------------------------------------------------
# Home
# ------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/Register')
def Register():
    return render_template('register.html')

@app.route('/Login')
def Login():
    return render_template('login.html')

@app.route('/OwnerDashboard')
def OwnerDashboard():
    return render_template('owner_dashboard.html')

@app.route("/upload")
def upload():
    return render_template('upload.html')

@app.route('/VerifierDashboard')
def VerifierDashboard():
    return render_template('verifier_dashboard.html')

@app.route('/files')
def files():
    return render_template('files.html')





# ------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
