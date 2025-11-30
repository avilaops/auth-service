# 🔐 Auth Service

Serviço centralizado de autenticação JWT para toda a plataforma Ávila Inc - Compartilhado entre Portal, ArkanaStore e outros projetos.

## 🚀 Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Rodar localmente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ou com Docker
docker build -t avilaops/auth-service .
docker run -p 8000:8000 --env-file .env avilaops/auth-service
```

## 📚 API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/verify-email` - Verify email
- `POST /auth/refresh` - Refresh access token
- `POST /auth/password-reset` - Request password reset
- `POST /auth/password-reset/confirm` - Confirm password reset
- `POST /auth/logout` - Logout user

### Users

- `GET /users/me` - Get current user profile
- `GET /users/{user_id}` - Get user by ID

### System

- `GET /` - Service info
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - OpenAPI documentation

## 🔒 Security

- JWT tokens (access + refresh)
- Bcrypt password hashing
- Email verification
- Password reset flow
- Token revocation via Redis
- Rate limiting

## 🗄️ Database Schema

```javascript
// MongoDB - users collection
{
  _id: ObjectId,
  email: String (unique),
  full_name: String,
  hashed_password: String,
  is_active: Boolean,
  is_verified: Boolean,
  created_at: DateTime,
  updated_at: DateTime
}
```

## 📊 Monitoring

Prometheus metrics disponíveis em `/metrics`

## 🐳 Docker Compose

```yaml
auth-service:
  image: avilaops/auth-service:latest
  environment:
    MONGODB_URI: mongodb://user:pass@mongodb:27017/auth
    REDIS_URL: redis://:password@redis:6379/0
    JWT_SECRET: ${JWT_SECRET}
```

## 📝 Licença

MIT - Ávila Inc © 2025
