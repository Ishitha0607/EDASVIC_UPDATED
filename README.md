# EDASVIC – Blockchain Based Storage Verification System

EDASVIC (Efficient Data Storage and Verification using IPFS and Blockchain) is a secure file storage and verification system developed using Blockchain technology, IPFS, and Flask. The project ensures data integrity by storing file details on the blockchain and using IPFS for decentralized file storage.

## Features

- Secure file upload and storage
- Decentralized storage using IPFS
- Blockchain-based verification
- User registration and login system
- Owner and verifier dashboards
- File integrity checking
- Smart contract integration
- Secure document management

## Technologies Used

- Frontend
  - HTML
  - CSS
  - JavaScript

- Backend
  - Python
  - Flask

- Blockchain
  - Solidity
  - Truffle
  - Ganache

- Storage
  - IPFS (InterPlanetary File System)

- Database / Files
  - CSV
  - Local storage

## Project Structure

```
EDASVIC/
│
├── app.py
├── contracts/
│   ├── EDASVIC.sol
│   └── Migrations.sol
│
├── migrations/
│
├── build/contracts/
│
├── static/
│   ├── styles.css
│   └── chunks/
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── owner_dashboard.html
│   ├── verifier_dashboard.html
│   └── verify_result.html
│
├── uploads/
└── truffle-config.js
```

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/EDASVIC.git
cd EDASVIC
```

### 2. Install Dependencies

```bash
pip install flask
pip install web3
pip install ipfshttpclient
```

### 3. Start Ganache

Open Ganache and start the local blockchain server.

### 4. Deploy Smart Contract

```bash
truffle migrate
```

### 5. Start IPFS

Run:

```bash
Start_IPFS.bat
```

or

```bash
ipfs daemon
```

### 6. Run Application

```bash
python app.py
```

Open browser:

```bash
http://127.0.0.1:5000
```

## Workflow

1. User registers and logs in
2. Uploads files into the system
3. File is stored in IPFS
4. Hash value is generated
5. Hash is stored on blockchain
6. Verifier checks integrity
7. System validates file authenticity

## Advantages

- Improved security
- Prevents data tampering
- Decentralized storage
- Easy verification process
- Better transparency
- Reduced risk of data loss

## Future Enhancements

- Cloud integration
- AI-based anomaly detection
- Multi-factor authentication
- Real-time notifications
- Enhanced encryption techniques

## Team Member

- Ishitha Bahunuthala

## License

This project is developed for educational and academic purposes.
