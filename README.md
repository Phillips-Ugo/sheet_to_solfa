# 🎵 Sheet to Solfa

Convert PDF sheet music to tonic solfa notation using AI-powered optical music recognition.

![Sheet to Solfa](https://img.shields.io/badge/AI-Gemini%202.0-blue)
![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)

## ✨ Features

- **PDF Upload**: Upload scanned or digital sheet music PDFs
- **AI-Powered OMR**: Uses Google Gemini 2.0 Flash for accurate music recognition
- **Key Detection**: Automatically detects key signatures (major/minor)
- **Movable Do System**: Converts notes to tonic solfa using movable Do
- **Multiple Export Formats**: Download as TXT, JSON, or PDF
- **Beautiful UI**: Modern, responsive interface

## 🎯 How It Works

1. **Upload** a PDF of sheet music
2. **AI Analysis** - Gemini Vision extracts notes, key, and time signature
3. **Conversion** - Notes are mapped to solfa syllables (d r m f s l t)
4. **Download** - Get your solfa notation in multiple formats

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed

# Run the development server
npm run dev
```

Visit `http://localhost:3000` to use the app!

## 📁 Project Structure

```
sheet_to_solfa/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Configuration & storage
│   │   ├── models/         # Pydantic models
│   │   ├── pipeline/       # Processing pipeline
│   │   │   ├── omr/        # Optical Music Recognition
│   │   │   ├── solfa.py    # Solfa conversion
│   │   │   └── ...
│   │   └── workers/        # Background processing
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Pages
│   │   ├── components/    # React components
│   │   └── lib/           # API client
│   └── package.json
└── README.md
```

## 🎼 Solfa Notation Guide

| Symbol | Name | Scale Degree |
|--------|------|--------------|
| d | Do | 1 (tonic) |
| r | Re | 2 |
| m | Mi | 3 |
| f | Fa | 4 |
| s | Sol | 5 |
| l | La | 6 |
| t | Ti | 7 |
| ' | High octave | +8 |
| , | Low octave | -8 |
| - | Sustained | - |
| 0 | Rest | - |

## 🌐 Deployment

### Frontend (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL=<your-backend-url>`
5. Deploy!

### Backend (Railway/Render)

1. Create new project from GitHub
2. Set root directory to `backend`
3. Add environment variable: `GEMINI_API_KEY=<your-key>`
4. Deploy!

## 🔧 Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
DEBUG=false
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload PDF for processing |
| GET | `/api/jobs/{id}` | Get job status |
| GET | `/api/jobs/{id}/result` | Get conversion result |
| GET | `/api/export/{id}/{format}` | Download result (txt/json/pdf) |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - feel free to use this project for any purpose.

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for AI-powered music recognition
- [music21](https://web.mit.edu/music21/) for music theory calculations
- [Next.js](https://nextjs.org/) & [FastAPI](https://fastapi.tiangolo.com/) for the web framework
