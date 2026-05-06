# 🌐 NLP Data Collection App

A comprehensive web application for collecting and validating translations in NLP projects, built with FastAPI backend and Streamlit frontend. This app enables community-driven data collection for machine translation tasks, featuring user registration, translation submission, and peer validation.

## ✨ Features

- **User Management**: Register users with dialect-specific profiles (Hunza, Nagar, Yasin)
- **Translation Submission**: Submit translations for English source sentences in standardized Latin script
- **Community Validation**: Vote on translation accuracy with upvote/downvote system
- **Real-time Updates**: Automatic loading of next sentences/translations after submissions
- **Mobile-Friendly UI**: Responsive Streamlit interface with clean, intuitive design
- **PostgreSQL Integration**: Robust database backend with SQLAlchemy ORM
- **RESTful API**: FastAPI-powered backend with comprehensive endpoints
- **CORS Support**: Cross-origin resource sharing for seamless frontend-backend communication

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Git

### Clone the Repository

```bash
git clone https://github.com/your-username/nlp-data-collection-app.git
cd nlp-data-collection-app
```

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
   ```

3. Set up PostgreSQL database:
   - Create a new database named `nlp_app`
   - Update `DATABASE_URL` in `database.py` with your credentials:
     ```python
     DATABASE_URL = "postgresql+psycopg2://username:password@localhost/nlp_app"
     ```

### Frontend Setup

1. Install Streamlit:
   ```bash
   pip install streamlit requests
   ```

## 🚀 Usage

### Running the Backend

Start the FastAPI server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Running the Frontend

Launch the Streamlit app:

```bash
streamlit run frontend/app.py
```

Access the application at `http://localhost:8501`.

### Workflow

1. **Register**: Create a user account in the sidebar with username and dialect selection
2. **Submit Translations**: Navigate to the "Submit Translation" tab to translate random English sentences
3. **Review Translations**: Switch to the "Review Translations" tab to validate community submissions
4. **Vote**: Use thumbs up/down buttons to rate translation accuracy (cannot vote on own translations)

## 📚 API Documentation

### Endpoints

#### Users
- `POST /users/` - Register a new user
  - Body: `{"username": "string", "dialect": "HUNZA|NAGAR|YASIN"}`

#### Sentences
- `GET /sentences/random` - Fetch a random active source sentence

#### Translations
- `POST /translations/` - Submit a new translation
  - Body: `{"source_id": "uuid", "user_id": "uuid", "translated_text": "string"}`
- `GET /translations/unverified` - Get translations needing review (net_votes between -2 and 2)

#### Validations
- `POST /validations/` - Submit a vote on a translation
  - Body: `{"translation_id": "uuid", "user_id": "uuid", "vote": 1|-1}`

### Response Models

All endpoints return JSON responses with appropriate HTTP status codes and error messages.

## 🗄️ Database Schema

### Tables

#### Users
- `id` (UUID, Primary Key)
- `username` (String, Unique)
- `dialect` (Enum: HUNZA, NAGAR, YASIN)
- `trust_score` (Float, Default: 0.0)

#### Source Sentences
- `id` (UUID, Primary Key)
- `text` (String)
- `language` (String, Default: 'English')
- `is_active` (Boolean, Default: True)

#### Translations
- `id` (UUID, Primary Key)
- `source_id` (UUID, Foreign Key → Source Sentences)
- `user_id` (UUID, Foreign Key → Users)
- `translated_text` (String)
- `net_votes` (Integer, Default: 0)
- `is_verified` (Boolean, Default: False)

#### Validations
- `id` (UUID, Primary Key)
- `translation_id` (UUID, Foreign Key → Translations)
- `user_id` (UUID, Foreign Key → Users)
- `vote` (Integer, Check Constraint: 1 or -1)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to function signatures
- Write comprehensive docstrings
- Test API endpoints with tools like Postman or curl
- Ensure mobile responsiveness in Streamlit UI

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Frontend powered by [Streamlit](https://streamlit.io/)
- Database ORM using [SQLAlchemy](https://www.sqlalchemy.org/)
- PostgreSQL database with [psycopg2](https://www.psycopg.org/)

---

For questions or support, please open an issue on GitHub.