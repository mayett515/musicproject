# Music Album Review App

A full-stack web application that allows users to search for music albums, add them to their collection, and write reviews.

## Features

- User authentication (register, login, profile)
- Browse and search for albums
- Add albums to your collection
- Write and read reviews for albums
- Rate albums with a 5-star system
- Responsive UI with dark mode

## Technology Stack

### Frontend
- React.js
- React Router for navigation
- TailwindCSS for styling
- DaisyUI components
- Axios for API requests

### Backend
- Flask (Python)
- SQLAlchemy ORM
- JWT for authentication
- Discogs API for album data
- PostgreSQL database (production)
- SQLite database (development)

## Getting Started

### Prerequisites
- Node.js (v14+)
- Python (v3.8+)
- npm or yarn
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/music-album-review-app.git
cd music-album-review-app
```

2. Set up the backend:
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (create a .env file)
echo "DISCOGS_API_TOKEN=your_discogs_token" > .env
echo "SECRET_KEY=your_secret_key" >> .env
echo "DATABASE_URL=postgresql://username:password@localhost/dbname" >> .env

# Initialize the database
flask db init
flask db migrate
flask db upgrade
```

3. Set up the frontend:
```bash
# Install dependencies
npm install  # or: yarn install

# Start the development server
npm run dev  # or: yarn dev
```

4. Open your browser and navigate to:
```
http://localhost:10000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/user` - Get current user information

### Albums
- `GET /api/albums` - Get all albums
- `GET /api/albums/:id` - Get album by ID
- `POST /api/albums` - Add a new album

### Reviews
- `GET /api/reviews` - Get all reviews (can filter by album_id or user_id)
- `GET /api/reviews/:id` - Get review by ID
- `POST /api/reviews` - Add a new review

## Deployment

### Backend
The backend can be deployed on Render, Heroku, or any other platform that supports Python applications. Database migrations should be run automatically during deployment.

### Frontend
The frontend is built with Vite and can be deployed on Netlify, Vercel, or any other static site hosting service. The build command is `npm run build` and the publish directory is `dist`.

## Database Configuration

### Development
For development, SQLite is used as the default database. The database file is stored in the `data` directory.

### Production
For production, PostgreSQL is recommended. Set the `DATABASE_URL` environment variable to connect to your PostgreSQL database.

Example:
```
DATABASE_URL=postgresql://username:password@host:port/dbname
```

## Environment Variables

### Backend
- `SECRET_KEY` - Secret key for JWT token generation
- `DISCOGS_API_TOKEN` - Token for the Discogs API
- `DATABASE_URL` - PostgreSQL connection string (for production)

### Frontend
- `VITE_API_URL` - URL of the backend API

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.